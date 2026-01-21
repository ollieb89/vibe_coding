"""CLI entry point using Typer."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from corpus_analyzer import __version__
from corpus_analyzer.config import settings
from corpus_analyzer.core.database import CorpusDatabase
from corpus_analyzer.core.scanner import scan_directory
from corpus_analyzer.extractors import extract_document

app = typer.Typer(
    name="corpus-analyzer",
    help="Extract, categorize, analyze, and template documentation.",
    rich_markup_mode="rich",
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold blue]corpus-analyzer[/] v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option("--version", "-v", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    """Document Corpus Analyzer - Extract, categorize, and analyze docs."""
    pass


# CLI Groups
db_app = typer.Typer(help="Manage the corpus database.")
samples_app = typer.Typer(help="Manage document samples.")
templates_app = typer.Typer(help="Manage document templates.")

app.add_typer(db_app, name="db")
app.add_typer(samples_app, name="samples")
app.add_typer(templates_app, name="templates")


@db_app.command("initialize")
def db_init(
    path: Annotated[Path, typer.Option("--path", "-p", help="Database path")] = settings.database_path,
) -> None:
    """Initialize the corpus database schema."""
    db = CorpusDatabase(path)
    db.initialize()
    console.print(f"[bold green]✓[/] Initialized database at {path}")


@db_app.command("inspect")
def db_inspect(
    path: Annotated[Path, typer.Option("--path", "-p", help="Database path")] = settings.database_path,
) -> None:
    """Inspect database schema and sample data."""
    from corpus_analyzer.utils.ui import print_sample_data, print_table_schema

    if not path.exists():
        console.print(f"[bold red]Error:[/] Database not found at {path}")
        raise typer.Exit(1)

    db = CorpusDatabase(path)
    tables = db.db.table_names()
    console.print(f"[bold blue]Tables:[/] {', '.join(tables)}\n")

    for table_name in tables:
        table = db.db[table_name]
        print_table_schema(table_name, table)
        print_sample_data(table_name, table)
        console.print()


@app.command()
def extract(
    source: Annotated[Path, typer.Argument(help="Source directory to scan")],
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Output database path")
    ] = settings.database_path,
    extensions: Annotated[
        Optional[list[str]],
        typer.Option("--ext", "-e", help="File extensions to include"),
    ] = None,
) -> None:
    """Extract documents from a directory into a corpus database."""
    if extensions is None:
        extensions = [".md", ".py", ".txt", ".rst"]

    console.print(f"[bold]Scanning[/] {source}")
    db = CorpusDatabase(output)
    db.initialize()

    file_count = 0
    for file_path in scan_directory(source, extensions):
        doc = extract_document(file_path, source)
        if doc:
            db.insert_document(doc)
            file_count += 1
            console.print(f"  [dim]Extracted:[/] {file_path.relative_to(source)}")

    console.print(f"\n[bold green]✓[/] Extracted {file_count} documents to {output}")


@app.command()
def classify(
    database: Annotated[Path, typer.Argument(help="Corpus database path")] = settings.database_path,
) -> None:
    """Classify documents by type and domain tags."""
    from corpus_analyzer.classifiers.document_type import classify_documents
    from corpus_analyzer.classifiers.domain_tags import tag_documents

    console.print(f"[bold]Classifying documents in[/] {database}")
    db = CorpusDatabase(database)

    classified = classify_documents(db)
    tagged = tag_documents(db)

    console.print(f"[bold green]✓[/] Classified {classified} documents")
    console.print(f"[bold green]✓[/] Tagged {tagged} documents")


@app.command()
def analyze(
    database: Annotated[Path, typer.Argument(help="Corpus database path")] = settings.database_path,
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Reports output directory")
    ] = settings.reports_dir,
) -> None:
    """Analyze document shapes and generate reports per category."""
    from corpus_analyzer.analyzers.shape import generate_shape_reports

    console.print(f"[bold]Analyzing shapes from[/] {database}")
    output.mkdir(parents=True, exist_ok=True)

    reports = generate_shape_reports(CorpusDatabase(database), output)
    console.print(f"[bold green]✓[/] Generated {len(reports)} shape reports in {output}")


@app.command("analyze-quality")
def analyze_quality(
    database: Annotated[Path, typer.Argument(help="Corpus database path")] = settings.database_path,
) -> None:
    """Analyze document quality and mark gold standard patterns."""
    from corpus_analyzer.analyzers.quality import QualityAnalyzer

    console.print(f"[bold]Analyzing document quality in[/] {database}")
    db = CorpusDatabase(database)
    analyzer = QualityAnalyzer(db)
    
    count = analyzer.analyze_all()
    console.print(f"[bold green]✓[/] Analyzed {count} documents and marked gold standards")


@samples_app.command("extract")
def samples_extract(
    database: Annotated[Path, typer.Option("--db", "-d", help="Corpus database path")] = settings.database_path,
    output: Annotated[Path, typer.Option("--output", "-o", help="Output directory")] = Path("source_docs"),
    limit: Annotated[int, typer.Option("--limit", "-l", help="Samples per category")] = 2,
) -> None:
    """Extract representative samples for each category to a directory."""
    from corpus_analyzer.core.samples import extract_samples

    if not database.exists():
        console.print(f"[bold red]Error:[/] Database not found at {database}")
        raise typer.Exit(1)

    db = CorpusDatabase(database)
    count = extract_samples(db, output, limit)
    console.print(f"[bold green]✓[/] Extracted {count} samples to {output}")


@templates_app.command("generate")
def templates_generate(
    database: Annotated[Path, typer.Argument(help="Corpus database path")] = settings.database_path,
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Templates output directory")
    ] = settings.templates_dir,
) -> None:
    """Generate templates from shape analysis."""
    from corpus_analyzer.generators.templates import generate_from_analysis

    console.print(f"[bold]Generating templates from[/] {database}")
    output.mkdir(parents=True, exist_ok=True)

    templates = generate_from_analysis(CorpusDatabase(database), output)
    console.print(f"[bold green]✓[/] Generated {len(templates)} templates in {output}")


@templates_app.command("freeze")
def templates_freeze(
    templates_dir: Annotated[Path, typer.Option("--dir", "-d", help="Templates directory")] = settings.templates_dir,
) -> None:
    """Freeze templates with contracts."""
    from corpus_analyzer.generators.templates import TEMPLATE_CONTRACTS, TEMPLATES
    
    if not templates_dir.exists():
        console.print(f"[bold red]Error:[/] Templates directory not found at {templates_dir}")
        raise typer.Exit(1)

    for name in TEMPLATES:
        src = templates_dir / f"{name}.md"
        dst = templates_dir / f"{name}.v1.md"
        
        if src.exists():
            content = src.read_text()
            contract = TEMPLATE_CONTRACTS.get(name, "<!-- TEMPLATE CONTRACT -->")
            
            if contract in content:
                console.print(f"[yellow]Skipping {name}, already has contract[/]")
                continue

            new_content = f"{contract}\n\n{content}"
            dst.write_text(new_content)
            console.print(f"[green]✓[/] Froze {dst.name}")
        else:
            console.print(f"[yellow]Warning: {src.name} not found[/]")


@app.command()
def rewrite(
    database: Annotated[Path, typer.Argument(help="Corpus database path")] = settings.database_path,
    category: Annotated[str, typer.Option("--category", "-c", help="Document category to rewrite")] = "howto",
    model: Annotated[str, typer.Option("--model", "-m", help="Ollama model name")] = settings.ollama_model,
    output: Annotated[
        Optional[Path], typer.Option("--output", "-o", help="Output directory for rewritten docs")
    ] = None,
    optimized: Annotated[bool, typer.Option("--optimized", help="Use gold standard patterns for optimization")] = False,
) -> None:
    """Rewrite/consolidate documents using local LLM (Ollama)."""
    from corpus_analyzer.llm.rewriter import rewrite_category

    console.print(f"[bold]Rewriting[/] {category} [bold]documents with[/] {model}")

    if output is None:
        output = Path(f"output/{category}")
    output.mkdir(parents=True, exist_ok=True)

    result = rewrite_category(
        db=CorpusDatabase(database),
        category=category,
        model=model,
        output_dir=output,
        optimized=optimized,
    )
    
    if result.errors:
        for err in result.errors:
            console.print(f"[bold red]Error:[/] {err}")
    
    if result.warnings:
        console.print(f"\n[bold yellow]Warnings ({len(result.warnings)}):[/]")
        for warn in result.warnings[:10]:  # Limit displayed warnings
            console.print(f"  [yellow]⚠[/] {warn}")
        if len(result.warnings) > 10:
            console.print(f"  [dim]... and {len(result.warnings) - 10} more[/]")
            
    console.print(f"\n[bold green]✓[/] Rewrote {result.docs_processed} documents to {output}")


if __name__ == "__main__":
    app()
