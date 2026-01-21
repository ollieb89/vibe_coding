import json
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

import sqlite_utils

from corpus_analyzer.core.models import (
    Chunk,
    CodeBlock,
    Document,
    DocumentCategory,
    DomainTag,
    Heading,
    Link,
    PythonSymbol,
)


class CorpusDatabase:
    """SQLite database for storing the document corpus."""

    def __init__(self, path: Path) -> None:
        """Initialize database connection."""
        self.path = path
        self.db = sqlite_utils.Database(path)

    def initialize(self) -> None:
        """Create database schema."""
        # Documents table
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                relative_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                title TEXT NOT NULL,
                mtime TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                headings TEXT,  -- JSON
                links TEXT,  -- JSON
                code_blocks TEXT,  -- JSON
                token_estimate INTEGER DEFAULT 0,
                module_docstring TEXT,
                imports TEXT,  -- JSON
                symbols TEXT,  -- JSON
                is_cli INTEGER DEFAULT 0,
                category TEXT DEFAULT 'unknown',
                category_confidence REAL DEFAULT 0.0,
                domain_tags TEXT,  -- JSON
                quality_score REAL DEFAULT 0.0,
                is_gold_standard INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                heading TEXT,
                chunk_index INTEGER NOT NULL,
                token_estimate INTEGER DEFAULT 0,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            );

            CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
            CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);
            CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
        """)

    def insert_document(self, doc: Document) -> int:
        """Insert or update a document and return its ID."""
        data = self._doc_to_dict(doc)
        path_str = str(doc.path)

        # Check if document already exists by path
        existing = self.db.execute(
            "SELECT id FROM documents WHERE path = ?", [path_str]
        ).fetchone()

        if existing:
            doc_id = existing[0]
            # Delete existing chunks to avoid orphans/duplicates
            self.db["chunks"].delete_where("document_id = ?", [doc_id])
            # Update existing document
            self.db["documents"].update(doc_id, data, alter=True)
            return doc_id

        # If not exists, insert new
        self.db["documents"].insert(data, alter=True)
        return self.db.execute("SELECT last_insert_rowid()").fetchone()[0]

    def _doc_to_dict(self, doc: Document) -> dict:
        """Convert a Document model to a database dictionary."""
        return {
            "path": str(doc.path),
            "relative_path": doc.relative_path,
            "file_type": doc.file_type,
            "title": doc.title,
            "mtime": doc.mtime.isoformat(),
            "size_bytes": doc.size_bytes,
            "headings": json.dumps([h.model_dump() for h in doc.headings]),
            "links": json.dumps([l.model_dump() for l in doc.links]),
            "code_blocks": json.dumps([c.model_dump() for c in doc.code_blocks]),
            "token_estimate": doc.token_estimate,
            "module_docstring": doc.module_docstring,
            "imports": json.dumps(doc.imports),
            "symbols": json.dumps([s.model_dump() for s in doc.symbols]),
            "is_cli": 1 if doc.is_cli else 0,
            "category": doc.category.value,
            "category_confidence": doc.category_confidence,
            "domain_tags": json.dumps([t.value for t in doc.domain_tags]),
            "quality_score": doc.quality_score,
            "is_gold_standard": 1 if doc.is_gold_standard else 0,
        }

    def insert_chunk(self, chunk: Chunk) -> int:
        """Insert a chunk and return its ID."""
        data = {
            "document_id": chunk.document_id,
            "content": chunk.content,
            "heading": chunk.heading,
            "chunk_index": chunk.chunk_index,
            "token_estimate": chunk.token_estimate,
        }
        self.db["chunks"].insert(data)
        return self.db.execute("SELECT last_insert_rowid()").fetchone()[0]

    def get_documents(
        self,
        category: Optional[DocumentCategory] = None,
        file_type: Optional[str] = None,
    ) -> Iterator[Document]:
        """Retrieve documents with optional filtering."""
        query = "SELECT * FROM documents WHERE 1=1"
        params: list = []

        if category:
            query += " AND category = ?"
            params.append(category.value)
        if file_type:
            query += " AND file_type = ?"
            params.append(file_type)

        # Execute once and get column names from description
        cursor = self.db.execute(query, params)
        cols = [desc[0] for desc in cursor.description]

        for row in cursor.fetchall():
            yield self._row_to_document(dict(zip(cols, row)))

    def get_document_by_id(self, doc_id: int) -> Optional[Document]:
        """Get a single document by ID."""
        row = self.db.execute(
            "SELECT * FROM documents WHERE id = ?", [doc_id]
        ).fetchone()
        if row:
            cols = [desc[0] for desc in self.db.execute("SELECT * FROM documents LIMIT 0").description]
            return self._row_to_document(dict(zip(cols, row)))
        return None

    def update_document_classification(
        self,
        doc_id: int,
        category: DocumentCategory,
        confidence: float,
        domain_tags: Optional[list[DomainTag]] = None,
    ) -> None:
        """Update document classification."""
        data = {
            "category": category.value,
            "category_confidence": confidence,
        }
        if domain_tags is not None:
            data["domain_tags"] = json.dumps([t.value for t in domain_tags])

        self.db["documents"].update(doc_id, data, alter=True)

    def update_document_tags(self, doc_id: int, domain_tags: list[DomainTag]) -> None:
        """Update only document domain tags."""
        self.db["documents"].update(
            doc_id,
            {"domain_tags": json.dumps([t.value for t in domain_tags])},
            alter=True
        )

    def update_document_quality(
        self, doc_id: int, score: float, is_gold_standard: bool
    ) -> None:
        """Update document quality metrics."""
        self.db["documents"].update(
            doc_id,
            {
                "quality_score": score,
                "is_gold_standard": 1 if is_gold_standard else 0,
            },
            alter=True
        )

    def get_gold_standard_documents(
        self,
        category: Optional[DocumentCategory] = None,
        tag: Optional[DomainTag] = None,
    ) -> Iterator[Document]:
        """Retrieve gold standard documents."""
        query = "SELECT * FROM documents WHERE is_gold_standard = 1"
        params: list = []

        if category:
            query += " AND category = ?"
            params.append(category.value)
        if tag:
            # Domain tags are stored as JSON list, so we use LIKE or JSON_EACH
            # For simplicity with SQLite, we can use LIKE since it's a fixed set of tags
            query += " AND domain_tags LIKE ?"
            params.append(f'%"{tag.value}"%')

        cursor = self.db.execute(query, params)
        cols = [desc[0] for desc in cursor.description]

        for row in cursor.fetchall():
            yield self._row_to_document(dict(zip(cols, row)))

    def get_categories(self) -> list[str]:
        """Get all unique categories in the corpus."""
        rows = self.db.execute(
            "SELECT DISTINCT category FROM documents WHERE category != 'unknown'"
        ).fetchall()
        return [row[0] for row in rows]

    def count_by_category(self) -> dict[str, int]:
        """Count documents per category."""
        rows = self.db.execute(
            "SELECT category, COUNT(*) FROM documents GROUP BY category"
        ).fetchall()
        return {row[0]: row[1] for row in rows}

    def _row_to_document(self, row: dict) -> Document:
        """Convert a database row to a Document model."""
        return Document(
            id=row["id"],
            path=Path(row["path"]),
            relative_path=row["relative_path"],
            file_type=row["file_type"],
            title=row["title"],
            mtime=datetime.fromisoformat(row["mtime"]),
            size_bytes=row["size_bytes"],
            headings=[Heading(**h) for h in json.loads(row["headings"] or "[]")],
            links=[Link(**l) for l in json.loads(row.get("links") or "[]")],
            code_blocks=[CodeBlock(**c) for c in json.loads(row.get("code_blocks") or "[]")],
            token_estimate=int(row.get("token_estimate") or 0),
            module_docstring=row.get("module_docstring"),
            imports=json.loads(row.get("imports") or "[]"),
            symbols=[PythonSymbol(**s) for s in json.loads(row.get("symbols") or "[]")],
            is_cli=bool(row.get("is_cli", 0)),
            category=DocumentCategory(row.get("category", "unknown")),
            category_confidence=float(row.get("category_confidence") if row.get("category_confidence") is not None else 0.0),
            domain_tags=[DomainTag(t) for t in json.loads(row.get("domain_tags") or "[]")],
            quality_score=float(row.get("quality_score") if row.get("quality_score") is not None else 0.0),
            is_gold_standard=bool(row.get("is_gold_standard") if row.get("is_gold_standard") is not None else 0),
        )
