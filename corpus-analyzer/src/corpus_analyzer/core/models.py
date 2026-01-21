"""Pydantic models for documents and chunks."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class DocumentCategory(str, Enum):
    """Document type classification categories."""

    PERSONA = "persona"
    HOWTO = "howto"
    RUNBOOK = "runbook"
    ARCHITECTURE = "architecture"
    REFERENCE = "reference"
    TUTORIAL = "tutorial"
    ADR = "adr"
    SPEC = "spec"
    UNKNOWN = "unknown"


class DomainTag(str, Enum):
    """Domain/topic tags for documents."""

    BACKEND = "backend"
    FRONTEND = "frontend"
    GRAPHQL = "graphql"
    TESTING = "testing"
    TEMPORAL = "temporal"
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    NEXTJS = "nextjs"
    REACT = "react"
    UV = "uv"
    DATABASE = "database"
    DEVOPS = "devops"
    SECURITY = "security"
    AI = "ai"
    OTHER = "other"


class CodeBlock(BaseModel):
    """A code block extracted from a document."""

    language: str = ""
    content: str
    content_hash: str
    line_start: int
    line_end: int


class Heading(BaseModel):
    """A heading extracted from a document."""

    level: int
    text: str
    line_number: int


class Link(BaseModel):
    """An outgoing link from a document."""

    text: str
    url: str
    line_number: int


class PythonSymbol(BaseModel):
    """A Python class or function."""

    name: str
    kind: str  # "class" | "function" | "method"
    docstring: Optional[str] = None
    line_start: int
    line_end: int


class Chunk(BaseModel):
    """A chunk/section of a document."""

    id: Optional[int] = None
    document_id: int
    content: str
    heading: Optional[str] = None
    chunk_index: int
    token_estimate: int = 0


class Document(BaseModel):
    """A document in the corpus."""

    id: Optional[int] = None
    path: Path
    relative_path: str
    file_type: str  # md, py, txt, rst
    title: str
    mtime: datetime
    size_bytes: int

    # Extracted metadata
    headings: list[Heading] = Field(default_factory=list)
    links: list[Link] = Field(default_factory=list)
    code_blocks: list[CodeBlock] = Field(default_factory=list)
    token_estimate: int = 0

    # Python-specific
    module_docstring: Optional[str] = None
    imports: list[str] = Field(default_factory=list)
    symbols: list[PythonSymbol] = Field(default_factory=list)
    is_cli: bool = False  # argparse/click/typer detection

    # Classification
    category: DocumentCategory = DocumentCategory.UNKNOWN
    category_confidence: float = 0.0
    domain_tags: list[DomainTag] = Field(default_factory=list)

    # Quality metrics
    quality_score: float = 0.0
    is_gold_standard: bool = False

    # Chunks (populated separately)
    chunks: list[Chunk] = Field(default_factory=list)
