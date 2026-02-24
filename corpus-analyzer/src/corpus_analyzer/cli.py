"""CLI entry point using Typer."""

import json as json_module
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from corpus_analyzer import __version__
from corpus_analyzer.config import SourceConfig, load_config, save_config
from corpus_analyzer.config.schema import CONFIG_PATH, DATA_DIR
from corpus_analyzer.core.database import CorpusDatabase
from corpus_analyzer.core.scanner import scan_directory
from corpus_analyzer.core.utils import file_content_hash, get_file_mtime
from corpus_analyzer.extractors import extract_document
from corpus_analyzer.graph.registry import SlugRegistry
from corpus_analyzer.graph.store import GraphStore
from corpus_analyzer.ingest.embedder import OllamaEmbedder
from corpus_analyzer.ingest.indexer import CorpusIndex, SourceStatus
from corpus_analyzer.ingest.scanner import walk_source
from corpus_analyzer.search.engine import CorpusSearch
from corpus_analyzer.search.formatter import extract_snippet
from corpus_analyzer.settings import settings as app_settings

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
        bool | None,
        typer.Option("--version", "-v", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    """Document Corpus Analyzer - Extract, categorize, and analyze docs."""
    pass


@app.command("add")
def add_command(
    directory: Annotated[str, typer.Argument(help="Directory path to add as a source")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="Source name (default: directory basename)")] = None,
    include: Annotated[list[str], typer.Option("--include", help="Glob patterns to include")] = ["**/*"],
    exclude: Annotated[list[str], typer.Option("--exclude", help="Glob patterns to exclude")] = [],
    force: Annotated[bool, typer.Option("--force", help="Re-add if source already exists")] = False,
) -> None:
    """Add a directory to corpus.toml as a named source."""
    # Resolve source name
    source_name = name if name else Path(directory).name

    # Load config
    config = load_config(CONFIG_PATH)

    # Check for duplicates
    existing_by_name = next((s for s in config.sources if s.name == source_name), None)
    existing_by_path = next((s for s in config.sources if s.path == directory), None)

    if (existing_by_name or existing_by_path) and not force:
        console.print(f"[red]Error:[/] Source '{source_name}' or path '{directory}' already exists. Use --force to re-add.")
        raise typer.Exit(code=1)

    # If force, remove existing
    if force:
        config.sources = [s for s in config.sources if s.name != source_name and s.path != directory]

    # Add new source
    config.sources.append(SourceConfig(
        name=source_name,
        path=directory,
        include=list(include),
        exclude=list(exclude),
    ))

    # Save config
    save_config(CONFIG_PATH, config)

    console.print(f"[green]✔[/] Added source '[bold]{source_name}[/]' ({directory})")
    console.print("  Run [bold]corpus index[/] to index it.")


@app.command("index")
def index_command(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Print each file as it is processed")] = False,
) -> None:
    """Index all configured sources into LanceDB."""
    # Load config
    config = load_config(CONFIG_PATH)

    if not config.sources:
        console.print("[yellow]No sources configured. Run 'corpus add <dir>' first.[/]")
        raise typer.Exit(code=0)

    # Validate Ollama connection
    embedder = OllamaEmbedder(model=config.embedding.model, host=config.embedding.host)
    try:
        embedder.validate_connection()
    except RuntimeError as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(code=1) from e

    # Open index
    index = CorpusIndex.open(DATA_DIR, embedder)

    # Build graph store and slug registry once for the whole run
    graph_store = GraphStore(DATA_DIR / "graph.sqlite")
    source_roots = [Path(s.path) for s in config.sources]
    registry = SlugRegistry.build(source_roots)
    if len(registry) == 0:
        console.print("[dim]Graph registry: no component directories found.[/]")
    for dup_slug, dup_paths in registry.duplicates.items():
        console.print(
            f"[yellow]⚠️  Duplicate slug detected: '{dup_slug}' "
            f"({len(dup_paths)} candidates — use fully-qualified paths to disambiguate)[/]"
        )

    # Index each source
    for source in config.sources:
        source_path = Path(source.path).expanduser()

        # Validate source path exists
        if not source_path.exists():
            console.print(f"[yellow]Warning:[/] Source path not found: {source.path} — skipping")
            continue

        # Pre-check: skip sources that haven't changed (no filesystem walk needed)
        status = index.check_source_status(source)
        if not status.needs_indexing:
            console.print(f"[dim]  - {source.name}: up to date[/]")
            continue

        # Show active extensions only on first run (onboarding/diagnostic signal)
        if status.reason == "new source":
            ext_str = ", ".join(source.extensions) if source.extensions else "(none — all files skipped)"
            console.print(
                f"[dim]Active extensions for {source.name}: {ext_str}[/dim]\n"
                f"[dim]Add 'extensions = [...]' to this source in corpus.toml to customize.[/dim]"
            )

        # Count total files for progress bar
        total = sum(
            1 for _ in walk_source(
                source_path,
                source.include,
                source.exclude,
                extensions=source.extensions,
            )
        )

        if total == 0:
            console.print(f"[yellow]Warning:[/] No files found in source: {source.name}")
            continue

        # Progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total} files"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task(f"Indexing {source.name}...", total=total)

            def progress_callback(n: int) -> None:
                progress.advance(task_id, n)

            result = index.index_source(
                source,
                progress_callback=progress_callback,
                graph_store=graph_store,
                registry=registry,
            )

        # Print summary
        console.print(
            f"[green]✔[/] Indexed [bold]{source.name}[/]: "
            f"{result.files_indexed} files, {result.chunks_written} chunks "
            f"({result.elapsed:.1f}s) — {result.files_skipped} unchanged"
        )
        if result.files_removed > 0:
            console.print(
                f"[yellow]Removed {result.files_removed} file(s) no longer in extension allowlist.[/]"
            )


@app.command("check")
def check_command(
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON for scripting")] = False,
) -> None:
    """Check which sources need indexing without modifying any state."""
    config = load_config(CONFIG_PATH)

    if not config.sources:
        if json_output:
            console.print(json_module.dumps([]))
        else:
            console.print("[yellow]No sources configured. Run 'corpus add <dir>' first.[/]")
        raise typer.Exit(code=0)

    embedder = OllamaEmbedder(model=config.embedding.model, host=config.embedding.host)

    try:
        index = CorpusIndex.open(DATA_DIR, embedder)
    except Exception:
        if json_output:
            console.print(json_module.dumps({"error": "Index not initialised. Run 'corpus index' first."}))
        else:
            console.print("[yellow]Index not initialised. Run 'corpus index' first.[/]")
        raise typer.Exit(code=0) from None

    statuses: list[SourceStatus] = []
    for source in config.sources:
        statuses.append(index.check_source_status(source))

    if json_output:
        console.print(
            json_module.dumps(
                [
                    {
                        "name": s.source_name,
                        "needs_indexing": s.needs_indexing,
                        "reason": s.reason,
                        "last_indexed_at": s.last_indexed_at,
                        "file_count": s.file_count,
                    }
                    for s in statuses
                ],
                indent=2,
            )
        )
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Source")
    table.add_column("Status")
    table.add_column("Reason")
    table.add_column("Last Indexed")
    table.add_column("Files", justify="right")

    for s in statuses:
        if s.needs_indexing:
            status_cell = "[yellow]⚠ needs indexing[/]"
        else:
            status_cell = "[green]✔ up to date[/]"

        last_indexed = s.last_indexed_at if s.last_indexed_at else "[dim]never[/]"
        file_count = str(s.file_count) if s.file_count else "[dim]—[/]"
        table.add_row(s.source_name, status_cell, s.reason, last_indexed, file_count)

    console.print(table)


@app.command("search")
def search_command(
    query: Annotated[str, typer.Argument(help="Natural language search query")],
    source: Annotated[str | None, typer.Option("--source", "-s", help="Filter by source name")] = None,
    type_: Annotated[str | None, typer.Option("--type", "-t", help="Filter by file type (.md, .py, etc.)")] = None,
    construct: Annotated[str | None, typer.Option("--construct", "-c", help="Filter by construct type (agent, skill, workflow, command, rule, prompt, code, documentation)")] = None,
    limit: Annotated[int, typer.Option("--limit", "-n", help="Maximum number of results")] = 10,
    sort: Annotated[str, typer.Option("--sort", help="Sort order: relevance|construct|confidence|date|path")] = "relevance",
) -> None:
    """Search the indexed corpus with a natural language query."""
    config = load_config(CONFIG_PATH)

    embedder = OllamaEmbedder(model=config.embedding.model, host=config.embedding.host)
    try:
        embedder.validate_connection()
    except RuntimeError as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(code=1)

    index = CorpusIndex.open(DATA_DIR, embedder)
    search = CorpusSearch(index.table, embedder)

    try:
        results = search.hybrid_search(
            query,
            source=source,
            file_type=type_,
            construct_type=construct,
            limit=limit,
            sort_by=sort,
        )
    except ValueError as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(code=1) from e

    if not results:
        console.print(f'[yellow]No results for "[bold]{query}[/bold]"[/yellow]')
        return

    if construct and sort == "construct":
        console.print(
            f"[dim]Note: Results already limited to '{construct}'; sorting by priority is implicit.[/]"
        )

    for result in results:
        console.print(
            f"[bold blue]{result['file_path']}[/]  "
            f"[dim]{result.get('construct_type') or 'documentation'}[/]  "
            f"[dim]score: {result.get('_relevance_score', 0.0):.3f}[/]"
        )
        if result.get("summary"):
            console.print(f"  [italic]{result['summary']}[/italic]")
        console.print(f"  {extract_snippet(str(result['text']), query)}")
        console.print()


@app.command("graph")
def graph_command(
    slug: Annotated[str, typer.Argument(help="Component slug or path fragment to look up")],
    depth: Annotated[int, typer.Option("--depth", "-d", help="Traversal depth")] = 1,
) -> None:
    """Show upstream and downstream relationships for a component."""
    if depth != 1:
        console.print("[yellow]Note: --depth > 1 not yet implemented, showing depth=1.[/yellow]")
    graph_db = DATA_DIR / "graph.sqlite"
    if not graph_db.exists():
        console.print("[yellow]No graph index found. Run 'corpus index' first.[/yellow]")
        raise typer.Exit(code=1)

    store = GraphStore(graph_db)

    # Resolve slug to paths by substring match
    matching_sources = store.search_paths(slug)

    if not matching_sources:
        console.print(f"[yellow]No relationships found for '[bold]{slug}[/bold]'.[/yellow]")
        return

    for source in sorted(matching_sources):
        downstream = store.edges_from(source)
        upstream = store.edges_to(source)
        console.print(f"\n[bold blue]{Path(source).parent.name}[/] ([dim]{source}[/])")
        if upstream:
            console.print("  [dim]Upstream (depends on this):[/]")
            for e in upstream:
                name = Path(e["source_path"]).parent.name
                flag = "" if e["resolved"] else " [dim](unresolved)[/]"
                console.print(f"    \u2190 {name}{flag}")
        if downstream:
            console.print("  [dim]Downstream (this depends on):[/]")
            for e in downstream:
                name = Path(e["target_path"]).parent.name
                flag = "" if e["resolved"] else " [dim](unresolved)[/]"
                console.print(f"    \u2192 {name}{flag}")


def _human_age(ts: str) -> str:
    """Convert ISO timestamp to human-readable age string ('2 hours ago')."""
    try:
        dt = datetime.fromisoformat(ts).replace(tzinfo=UTC)
        delta = datetime.now(UTC) - dt
        secs = int(delta.total_seconds())
        if secs < 60:
            return f"{secs} seconds ago"
        elif secs < 3600:
            return f"{secs // 60} minutes ago"
        elif secs < 86400:
            return f"{secs // 3600} hours ago"
        else:
            return f"{secs // 86400} days ago"
    except Exception:
        return ts


def _count_stale_files(source: SourceConfig, indexed_at: str) -> int:
    """Count files in source directory modified after the last index time."""
    try:
        indexed_dt = datetime.fromisoformat(indexed_at)
        source_path = Path(source.path).expanduser()
        return sum(
            1 for fp in walk_source(source_path, source.include, source.exclude, extensions=source.extensions)
            if fp.stat().st_mtime > indexed_dt.timestamp()
        )
    except Exception:
        return 0


@app.command("status")
def status_command(
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON for scripting")] = False,
) -> None:
    """Show index health: sources, staleness, chunk count, embedding model status."""
    config = load_config(CONFIG_PATH)
    embedder = OllamaEmbedder(model=config.embedding.model, host=config.embedding.host)

    # Test model reachability
    try:
        embedder.validate_connection()
        model_status = "connected"
    except RuntimeError:
        model_status = "unreachable"

    # Open index and get stats
    try:
        index = CorpusIndex.open(DATA_DIR, embedder)
        search = CorpusSearch(index.table, embedder)
        stats = search.status(config.embedding.model)
    except Exception:
        if json_output:
            console.print(json_module.dumps({"error": "Index not found. Run 'corpus index' first."}))
        else:
            console.print("[yellow]Index not found. Run 'corpus index' first.[/]")
        raise typer.Exit(code=0) from None

    last_indexed = str(stats.get("last_indexed", "never"))
    files_total = int(stats.get("files", 0))
    chunks_total = int(stats.get("chunks", 0))

    # Per-source staleness
    source_rows = []
    total_stale = 0
    for source in config.sources:
        stale_count = _count_stale_files(source, last_indexed) if last_indexed != "never" else 0
        total_stale += stale_count
        source_rows.append({
            "name": source.name,
            "path": source.path,
            "stale_files": stale_count,
            "health": "current" if stale_count == 0 else "stale",
        })

    db_path = DATA_DIR / "corpus.lance"
    db_size = db_path.stat().st_size if db_path.exists() else 0

    if json_output:
        output_data = {
            "health": "current" if total_stale == 0 else "stale",
            "files": files_total,
            "chunks": chunks_total,
            "last_indexed": last_indexed,
            "stale_files": total_stale,
            "model": {
                "name": config.embedding.model,
                "status": model_status,
            },
            "sources": source_rows,
            "database": {
                "path": str(DATA_DIR),
                "size_bytes": db_size,
            },
        }
        console.print(json_module.dumps(output_data, indent=2))
        return

    # Rich table output
    age_str = _human_age(last_indexed) if last_indexed != "never" else "never"
    health_str = "[green]OK[/green]" if total_stale == 0 else f"[yellow]{total_stale} files changed since last index[/yellow]"
    model_str = f"{config.embedding.model}  [green]connected[/]" if model_status == "connected" else f"{config.embedding.model}  [red]unreachable[/]"

    table = Table(title="[bold]Index Status[/]", show_header=True)
    table.add_column("Metric", style="bold", min_width=18)
    table.add_column("Value")
    table.add_row("Health", health_str)
    table.add_row("Files", str(files_total))
    table.add_row("Chunks", str(chunks_total))
    table.add_row("Last indexed", f"{last_indexed}  [dim]({age_str})[/dim]")
    table.add_row("Model", model_str)
    table.add_row("Database", str(DATA_DIR))
    console.print(table)

    if source_rows:
        src_table = Table(title="[bold]Sources[/]", show_header=True)
        src_table.add_column("Name", style="bold")
        src_table.add_column("Path")
        src_table.add_column("Status")
        for row in source_rows:
            icon = "[green]current[/]" if row["stale_files"] == 0 else f"[yellow]{row['stale_files']} stale[/]"
            src_table.add_row(str(row["name"]), str(row["path"]), icon)
        console.print(src_table)


# CLI Groups
db_app = typer.Typer(help="Manage the corpus database.")
samples_app = typer.Typer(help="Manage document samples.")
templates_app = typer.Typer(help="Manage document templates.")
mcp_app = typer.Typer(help="MCP server commands.")

app.add_typer(db_app, name="db")
app.add_typer(samples_app, name="samples")
app.add_typer(templates_app, name="templates")
app.add_typer(mcp_app, name="mcp")


@mcp_app.command("serve")
def mcp_serve() -> None:
    """Start the corpus MCP server over stdio (for Claude Code and other MCP clients).

    Register with Claude Code:
        { "command": "corpus", "args": ["mcp", "serve"] }
    """
    from corpus_analyzer.mcp.server import mcp  # lazy import

    mcp.run()  # defaults to stdio transport


@db_app.command("initialize")
def db_init(
    path: Annotated[Path, typer.Option("--path", "-p", help="Database path")] = app_settings.database_path,
) -> None:
    """Initialize the corpus database schema."""
    db = CorpusDatabase(path)
    db.initialize()
    console.print(f"[bold green]✓[/] Initialized database at {path}")


@db_app.command("inspect")
def db_inspect(
    path: Annotated[Path, typer.Option("--path", "-p", help="Database path")] = app_settings.database_path,
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
    ] = app_settings.database_path,
    extensions: Annotated[
        list[str] | None,
        typer.Option("--ext", "-e", help="File extensions to include"),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Re-extract all files, ignoring cached fingerprints"),
    ] = False,
) -> None:
    """Extract documents from a directory into a corpus database.

    Files that are already indexed and whose content has not changed since the last
    extraction are skipped automatically.  Pass --force to bypass this check and
    re-process every file regardless.
    """
    if extensions is None:
        extensions = [".md", ".py", ".txt", ".rst"]

    console.print(f"[bold]Scanning[/] {source}")
    if force:
        console.print("[yellow]--force: skipping change-detection cache[/]")

    db = CorpusDatabase(output)
    db.initialize()

    count_new = 0
    count_updated = 0
    count_skipped = 0

    for file_path in scan_directory(source, extensions):
        path_str = str(file_path)
        rel = file_path.relative_to(source)

        # Determine whether to skip this file and whether it is new vs updated.
        # resolved_hash / resolved_mtime are lazily computed and reused below.
        resolved_hash: str | None = None
        resolved_mtime: float | None = None
        is_new = True

        if not force:
            fingerprint = db.get_file_fingerprint(path_str)
            if fingerprint is not None:
                stored_hash, stored_mtime = fingerprint
                # Treat a blank hash as "not yet fingerprinted" (legacy migrated row);
                # skip tier checks and re-extract so it gets a proper fingerprint.
                is_new = not stored_hash
                if stored_hash:
                    resolved_mtime = get_file_mtime(file_path)

                    # Tier 1: mtime unchanged → skip without reading file content
                    if resolved_mtime == stored_mtime:
                        count_skipped += 1
                        continue

                    # Tier 2: mtime changed → verify via content hash
                    resolved_hash = file_content_hash(file_path)
                    if resolved_hash == stored_hash:
                        # Content identical; update stored mtime to avoid future hash reads
                        db.update_file_fingerprint(path_str, resolved_hash, resolved_mtime)
                        count_skipped += 1
                        continue

                    # Tier 3: content changed → fall through to re-extract

        doc = extract_document(file_path, source)
        if doc:
            # Reuse already-computed hash/mtime where available; otherwise compute now.
            doc.content_hash = (
                resolved_hash if resolved_hash is not None else file_content_hash(file_path)
            )
            doc.last_modified = (
                resolved_mtime if resolved_mtime is not None else get_file_mtime(file_path)
            )
            db.insert_document(doc)
            if is_new:
                count_new += 1
                console.print(f"  [dim]New:[/]      {rel}")
            else:
                count_updated += 1
                console.print(f"  [dim]Updated:[/]  {rel}")

    total = count_new + count_updated
    console.print(
        f"\n[bold green]✓[/] {total} extracted ({count_new} new, {count_updated} updated), "
        f"[dim]{count_skipped} unchanged[/] — {output}"
    )


@app.command()
def classify(
    database: Annotated[Path, typer.Argument(help="Corpus database path")] = app_settings.database_path,
    use_full_content: Annotated[bool, typer.Option("--full-content", help="Use full document content for better classification")] = True,
) -> None:
    """Classify documents by type and domain tags with enhanced analysis."""
    from corpus_analyzer.classifiers.document_type import classify_documents
    from corpus_analyzer.classifiers.domain_tags import tag_documents

    console.print(f"[bold]Classifying documents in[/] {database}")
    if use_full_content:
        console.print("[dim]Using full content analysis for enhanced classification[/]")

    db = CorpusDatabase(database)

    classified = classify_documents(db, use_full_content=use_full_content)
    tagged = tag_documents(db)

    console.print(f"[bold green]✓[/] Classified {classified} documents")
    console.print(f"[bold green]✓[/] Tagged {tagged} documents")


@app.command()
def analyze(
    database: Annotated[Path, typer.Argument(help="Corpus database path")] = app_settings.database_path,
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Reports output directory")
    ] = app_settings.reports_dir,
) -> None:
    """Analyze document shapes and generate reports per category."""
    from corpus_analyzer.analyzers.shape import generate_shape_reports

    console.print(f"[bold]Analyzing shapes from[/] {database}")
    output.mkdir(parents=True, exist_ok=True)

    reports = generate_shape_reports(CorpusDatabase(database), output)
    console.print(f"[bold green]✓[/] Generated {len(reports)} shape reports in {output}")


@app.command("analyze-quality")
def analyze_quality(
    database: Annotated[Path, typer.Argument(help="Corpus database path")] = app_settings.database_path,
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
    database: Annotated[Path, typer.Option("--db", "-d", help="Corpus database path")] = app_settings.database_path,
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
    database: Annotated[Path, typer.Argument(help="Corpus database path")] = app_settings.database_path,
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Templates output directory")
    ] = app_settings.templates_dir,
) -> None:
    """Generate templates from shape analysis."""
    from corpus_analyzer.generators.templates import generate_from_analysis

    console.print(f"[bold]Generating templates from[/] {database}")
    output.mkdir(parents=True, exist_ok=True)

    templates = generate_from_analysis(CorpusDatabase(database), output)
    console.print(f"[bold green]✓[/] Generated {len(templates)} templates in {output}")


@templates_app.command("freeze")
def templates_freeze(
    templates_dir: Annotated[Path, typer.Option("--dir", "-d", help="Templates directory")] = app_settings.templates_dir,
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
    database: Annotated[Path, typer.Argument(help="Corpus database path")] = app_settings.database_path,
    category: Annotated[str, typer.Option("--category", "-c", help="Document category to rewrite")] = "howto",
    model: Annotated[str, typer.Option("--model", "-m", help="Ollama model name")] = app_settings.ollama_model,
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Output directory for rewritten docs")
    ] = None,
    optimized: Annotated[bool, typer.Option("--optimized", help="Use gold standard patterns for optimization")] = False,
    use_templates: Annotated[bool, typer.Option("--templates", help="Use template-based rewriting")] = True,
    auto_category: Annotated[bool, typer.Option("--auto-category", help="Auto-select best category based on classification confidence")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show detailed progress information")] = False,
) -> None:
    """Rewrite/consolidate documents using enhanced unified rewriter."""
    from corpus_analyzer.core.models import DocumentCategory
    from corpus_analyzer.llm.unified_rewriter import UnifiedRewriter

    console.print(f"[bold]Rewriting[/] {category} [bold]documents with[/] {model}")

    db = CorpusDatabase(database)

    # Auto-select category if requested
    if auto_category:
        console.print("[dim]Analyzing classifications to auto-select best category...[/]")

        # Get classification statistics
        category_scores: dict[DocumentCategory, list[float]] = {}
        for doc in db.get_documents():
            if doc.id and doc.category != DocumentCategory.UNKNOWN:
                if doc.category not in category_scores:
                    category_scores[doc.category] = []
                category_scores[doc.category].append(doc.category_confidence)

        if category_scores:
            # Find category with highest average confidence and most documents
            best_category = max(
                category_scores.keys(),
                key=lambda c: (len(category_scores[c]), sum(category_scores[c]) / len(category_scores[c]))
            )
            avg_confidence = sum(category_scores[best_category]) / len(category_scores[best_category])

            console.print(f"[bold green]→[/] Auto-selected: {best_category.value} ({len(category_scores[best_category])} docs, {avg_confidence:.2f} avg confidence)")
            category = best_category.value
        else:
            console.print("[yellow]Warning: Could not auto-select category, using provided category[/]")

    if output is None:
        output = Path(f"output/{category}")
    output.mkdir(parents=True, exist_ok=True)

    # Show document count and estimated time
    doc_category = DocumentCategory(category)
    docs = list(db.get_documents(category=doc_category))
    total_docs = len(docs)

    if total_docs == 0:
        console.print(f"[yellow]No documents found in category: {category}[/]")
        return

    console.print(f"[bold]Processing {total_docs} documents[/] in category '{category}'")

    if verbose:
        # Show sample of documents to be processed
        console.print("\n[dim]Sample documents to be processed:[/]")
        for doc in docs[:5]:
            console.print(f"  • {doc.relative_path}")
        if len(docs) > 5:
            console.print(f"  ... and {len(docs) - 5} more")

    # Initialize unified rewriter
    rewriter = UnifiedRewriter(
        model=model,
        templates_dir=app_settings.templates_dir,
        use_templates=use_templates,
        use_llm_fallback=True
    )

    # Start rewrite with progress tracking
    console.print("\n[bold blue]Starting rewrite process...[/]")
    start_time = time.time()

    result = rewriter.rewrite_category(
        db=db,
        category=category,
        output_dir=output,
        optimized=optimized,
    )

    elapsed_time = time.time() - start_time

    # Show completion summary
    console.print(f"\n[bold green]✓ Rewrite completed in {elapsed_time:.1f} seconds[/]")

    if result.errors:
        console.print(f"\n[bold red]Errors ({len(result.errors)}):[/]")
        for err in result.errors[:10]:  # Limit displayed errors
            console.print(f"  [red]✗[/] {err}")
        if len(result.errors) > 10:
            console.print(f"  [dim]... and {len(result.errors) - 10} more[/]")

    if result.warnings:
        console.print(f"\n[bold yellow]Warnings ({len(result.warnings)}):[/]")
        for warn in result.warnings[:10]:  # Limit displayed warnings
            console.print(f"  [yellow]⚠[/] {warn}")
        if len(result.warnings) > 10:
            console.print(f"  [dim]... and {len(result.warnings) - 10} more[/]")

    # Show quality summary
    if result.quality_scores:
        avg_quality = sum(result.quality_scores.values()) / len(result.quality_scores)
        console.print("\n[bold]Quality Summary:[/]")
        console.print(f"  Average quality score: {avg_quality:.1f}/100")
        console.print(f"  Documents processed: {len(result.quality_scores)}")
        console.print(f"  Processing rate: {len(result.quality_scores)/elapsed_time:.2f} docs/sec")

        # Show best and worst
        if len(result.quality_scores) > 1:
            best_doc = max(result.quality_scores, key=lambda key: result.quality_scores[key])
            worst_doc = min(result.quality_scores, key=lambda key: result.quality_scores[key])
            console.print(f"  Best: {best_doc} ({result.quality_scores[best_doc]:.1f})")
            console.print(f"  Worst: {worst_doc} ({result.quality_scores[worst_doc]:.1f})")

    console.print(f"\n[bold green]✓[/] Rewrote {result.docs_processed} documents to {output}")


@app.command()
def review(
    database: Annotated[Path, typer.Argument(help="Corpus database path")] = app_settings.database_path,
    category: Annotated[str | None, typer.Option("--category", "-c", help="Filter by category")] = None,
    limit: Annotated[int, typer.Option("--limit", "-l", help="Number of docs to review")] = 10,
) -> None:
    """Manually review documents and mark as Gold Standard."""
    from corpus_analyzer.core.models import DocumentCategory

    db = CorpusDatabase(database)

    doc_category = None
    if category:
        try:
            doc_category = DocumentCategory(category)
        except ValueError as e:
            console.print(f"[bold red]Error:[/] Unknown category: {category}")
            raise typer.Exit(1) from e

    docs = list(db.get_documents(category=doc_category))
    # Filter out already gold standard? Or maybe allow toggling off?
    # Let's show non-gold first.
    docs = [d for d in docs if not d.is_gold_standard]

    if not docs:
        console.print("[yellow]No documents to review.[/]")
        return

    console.print(f"[bold]Found {len(docs)} documents to review.[/]")

    count = 0
    for doc in docs[:limit]:
        console.rule(f"[bold blue]{doc.title}[/]")
        console.print(f"Path: {doc.relative_path}")
        console.print(f"Category: {doc.category.value} (Confidence: {doc.category_confidence:.2f})")
        console.print(f"Quality Score: {doc.quality_score}")
        console.print(f"\n[dim]{doc.path.read_text()[:500]}...[/dim]\n")

        should_mark = typer.confirm(f"Mark '{doc.title}' as Gold Standard?")
        if should_mark:
            if doc.id is None:
                continue
            db.set_gold_standard(doc.id, True)
            console.print("[green]Marked as Gold Standard[/]")
            count += 1

        if not typer.confirm("Continue to next?"):
            break

    console.print(f"\n[bold green]✓[/] Marked {count} documents as gold standard.")


if __name__ == "__main__":
    app()
