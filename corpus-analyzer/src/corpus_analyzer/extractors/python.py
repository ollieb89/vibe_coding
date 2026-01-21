"""Python script/module extractor using AST."""

import ast
import hashlib
from datetime import datetime
from pathlib import Path

from corpus_analyzer.core.models import CodeBlock, Document, PythonSymbol
from corpus_analyzer.extractors.base import BaseExtractor


class PythonExtractor(BaseExtractor):
    """Extract metadata from Python files using AST analysis."""

    # CLI framework indicators
    CLI_INDICATORS = {
        "argparse",
        "click",
        "typer",
        "fire",
        "docopt",
    }

    def extract(self, file_path: Path, root: Path) -> Document:
        """Extract document from Python file."""
        content = file_path.read_text(encoding="utf-8", errors="replace")
        stat = file_path.stat()

        # Parse AST
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Return minimal document for unparseable files
            return Document(
                path=file_path,
                relative_path=str(file_path.relative_to(root)),
                file_type="py",
                title=file_path.stem,
                mtime=datetime.fromtimestamp(stat.st_mtime),
                size_bytes=stat.st_size,
                token_estimate=self.estimate_tokens(content),
            )

        # Extract module docstring
        module_docstring = ast.get_docstring(tree)

        # Extract imports
        imports = self._extract_imports(tree)

        # Detect CLI-ness
        is_cli = bool(self.CLI_INDICATORS & set(imports))

        # Extract symbols (classes, functions)
        symbols = self._extract_symbols(tree, content)

        # Create code blocks for the entire file
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        code_blocks = [
            CodeBlock(
                language="python",
                content=content,
                content_hash=content_hash,
                line_start=1,
                line_end=len(content.split("\n")),
            )
        ]

        # Generate title from module docstring or filename
        title = self._generate_title(module_docstring, file_path)

        return Document(
            path=file_path,
            relative_path=str(file_path.relative_to(root)),
            file_type="py",
            title=title,
            mtime=datetime.fromtimestamp(stat.st_mtime),
            size_bytes=stat.st_size,
            module_docstring=module_docstring,
            imports=imports,
            symbols=symbols,
            is_cli=is_cli,
            code_blocks=code_blocks,
            token_estimate=self.estimate_tokens(content),
        )

    def _extract_imports(self, tree: ast.AST) -> list[str]:
        """Extract all import statements."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split(".")[0])
        return list(set(imports))

    def _extract_symbols(self, tree: ast.AST, content: str) -> list[PythonSymbol]:
        """Extract classes and functions with their docstrings."""
        symbols = []
        lines = content.split("\n")

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                symbols.append(PythonSymbol(
                    name=node.name,
                    kind="class",
                    docstring=ast.get_docstring(node),
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                ))
                # Extract methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                        symbols.append(PythonSymbol(
                            name=f"{node.name}.{item.name}",
                            kind="method",
                            docstring=ast.get_docstring(item),
                            line_start=item.lineno,
                            line_end=item.end_lineno or item.lineno,
                        ))

            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                symbols.append(PythonSymbol(
                    name=node.name,
                    kind="function",
                    docstring=ast.get_docstring(node),
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                ))

        return symbols

    def _generate_title(self, docstring: str | None, file_path: Path) -> str:
        """Generate title from docstring or filename."""
        if docstring:
            # Use first line of docstring
            first_line = docstring.split("\n")[0].strip()
            if first_line:
                return first_line[:100]  # Limit length

        # Fall back to filename
        return file_path.stem.replace("_", " ").replace("-", " ").title()
