"""Markdown document extractor."""

import hashlib
import re
from datetime import datetime
from pathlib import Path

import frontmatter

from corpus_analyzer.core.models import CodeBlock, Document, Heading, Link
from corpus_analyzer.extractors.base import BaseExtractor


class MarkdownExtractor(BaseExtractor):
    """Extract metadata and content from Markdown files."""

    # Regex patterns
    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    CODE_BLOCK_PATTERN = re.compile(
        r"```(\w*)\n(.*?)```",
        re.MULTILINE | re.DOTALL,
    )

    def extract(self, file_path: Path, root: Path) -> Document:
        """Extract document from Markdown file."""
        content = file_path.read_text(encoding="utf-8", errors="replace")
        stat = file_path.stat()

        # Parse frontmatter
        try:
            post = frontmatter.loads(content)
            body = post.content
            metadata = post.metadata
        except Exception:
            # Fall back to treating entire content as body
            body = content
            metadata = {}

        # Extract title
        title = self._extract_title(body, metadata, file_path)

        # Extract headings
        headings = self._extract_headings(body)

        # Extract links
        links = self._extract_links(body)

        # Extract code blocks
        code_blocks = self._extract_code_blocks(body)

        return Document(
            path=file_path,
            relative_path=str(file_path.relative_to(root)),
            file_type=file_path.suffix.lstrip("."),
            title=title,
            mtime=datetime.fromtimestamp(stat.st_mtime),
            size_bytes=stat.st_size,
            headings=headings,
            links=links,
            code_blocks=code_blocks,
            token_estimate=self.estimate_tokens(body),
        )

    def _extract_title(
        self,
        content: str,
        metadata: dict,
        file_path: Path,
    ) -> str:
        """Extract title from frontmatter, first H1, or filename."""
        # Try frontmatter title
        if "title" in metadata:
            return str(metadata["title"])

        # Try first H1
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        # Fall back to filename
        return file_path.stem.replace("_", " ").replace("-", " ").title()

    def _extract_headings(self, content: str) -> list[Heading]:
        """Extract all headings with their hierarchy."""
        headings = []
        for line_num, line in enumerate(content.split("\n"), 1):
            match = self.HEADING_PATTERN.match(line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append(Heading(level=level, text=text, line_number=line_num))
        return headings

    def _extract_links(self, content: str) -> list[Link]:
        """Extract all markdown links."""
        links = []
        lines = content.split("\n")
        for line_num, line in enumerate(lines, 1):
            for match in self.LINK_PATTERN.finditer(line):
                links.append(Link(
                    text=match.group(1),
                    url=match.group(2),
                    line_number=line_num,
                ))
        return links

    def _extract_code_blocks(self, content: str) -> list[CodeBlock]:
        """Extract all code blocks with language detection."""
        code_blocks = []

        # Track line numbers
        lines = content.split("\n")
        current_pos = 0

        for match in self.CODE_BLOCK_PATTERN.finditer(content):
            language = match.group(1) or ""
            code = match.group(2)

            # Calculate line numbers
            start_pos = match.start()
            end_pos = match.end()
            line_start = content[:start_pos].count("\n") + 1
            line_end = content[:end_pos].count("\n") + 1

            # Hash the content for deduplication
            content_hash = hashlib.sha256(code.encode()).hexdigest()[:16]

            code_blocks.append(CodeBlock(
                language=language,
                content=code,
                content_hash=content_hash,
                line_start=line_start,
                line_end=line_end,
            ))

        return code_blocks
