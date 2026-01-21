"""Command-line interface for Agent Discovery System."""

import time
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def _parse_subject_top(values: tuple[str, ...]) -> dict[str, int]:
    """Convert subject=N entries into a mapping."""
    subject_top: dict[str, int] = {}
    for entry in values:
        if "=" not in entry:
            raise click.BadParameter("Use subject=N format, e.g., database=3")
        subject, count = entry.split("=", 1)
        subject = subject.strip()
        try:
            subject_top[subject] = int(count)
        except ValueError as exc:
            raise click.BadParameter(f"Invalid count for {subject}: {count}") from exc
    return subject_top


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """🔍 Agent Discovery System - Find the perfect agents for your codebase."""
    pass


@cli.command()
@click.option("--path", type=click.Path(exists=True), default=".", help="Path to codebase")
@click.option("--output", "-o", type=click.Path(), default=".", help="Output directory")
@click.option("--name", help="Project name for headers")
@click.option("--agents-only", is_flag=True, help="Generate only AGENTS.md")
@click.option(
    "--full",
    is_flag=True,
    default=True,
    help="Generate full package (AGENTS.md + instructions + chatmode)",
)
@click.option("--results", "-n", default=10, help="Number of agents to include")
@click.option(
    "--min-score",
    default=0.35,
    type=float,
    help="Minimum match score (0-1, default 0.35)",
)
@click.option(
    "--subject-top",
    multiple=True,
    help="Cap results per subject (e.g., --subject-top database=3)",
)
@click.option("--overwrite/--no-overwrite", default=False, help="Overwrite existing files")
@click.option("--dry-run", is_flag=True, help="Show what would be generated without writing")
def generate(
    path: str,
    output: str,
    name: str | None,
    agents_only: bool,
    full: bool,
    results: int,
    min_score: float | None,
    subject_top: tuple[str, ...],
    overwrite: bool,
    dry_run: bool,
):
    """📝 Generate AGENTS.md and configuration files from discovery results.

    Analyzes your codebase, discovers relevant agents, and generates:
    - AGENTS.md - Recommended agents with usage guide
    - .github/instructions/project.instructions.md - Project-specific guidelines
    - .github/chatmodes/project-assistant.chatmode.md - Custom chatmode

    Examples:
        agent-discover generate --path ./my-project
        agent-discover generate --path . --output ./docs --agents-only
        agent-discover generate --dry-run
    """
    from agent_discovery.discovery import DiscoveryEngine
    from agent_discovery.generator import OutputGenerator
    from agent_discovery.models import SearchCriteria

    console.print(
        Panel(
            "[bold blue]📝 Agent Configuration Generator[/bold blue]\n\n"
            "I'll analyze your codebase and generate agent configurations.",
            title="Generate",
        )
    )

    # Initialize engines
    engine = DiscoveryEngine()
    generator = OutputGenerator()

    # Analyze codebase
    console.print(f"\n[yellow]Step 1: Analyzing codebase at: {path}[/yellow]")
    try:
        profile = engine.analyze_codebase(path)
        console.print("[green]✓ Analysis complete[/green]")

        if profile.languages:
            console.print(f"  Languages: {', '.join(profile.languages)}")
        if profile.frameworks:
            console.print(f"  Frameworks: {', '.join(profile.frameworks)}")
        if profile.patterns:
            console.print(f"  Patterns: {', '.join(profile.patterns)}")
    except Exception as e:
        console.print(f"[yellow]⚠️ Could not analyze codebase: {e}[/yellow]")
        profile = None

    # Discover agents
    console.print("\n[yellow]Step 2: Discovering relevant agents...[/yellow]")

    criteria = SearchCriteria(
        detected_languages=profile.languages if profile else [],
        detected_frameworks=profile.frameworks if profile else [],
    )

    matches = engine.discover(
        criteria,
        n_results=results,
        min_score=min_score,
        subject_top_n=_parse_subject_top(subject_top),
    )

    if not matches:
        console.print("[red]No matching agents found. Ensure agents are ingested first.[/red]")
        console.print("[dim]Run: agent-discover ingest[/dim]")
        return

    console.print(f"[green]✓ Found {len(matches)} matching agents[/green]")

    # Generate files
    console.print("\n[yellow]Step 3: Generating configuration files...[/yellow]")

    project_name = name or (Path(path).resolve().name if path != "." else Path.cwd().name)

    if agents_only:
        files = {"AGENTS.md": generator.generate_agents_md(matches, profile, project_name)}
    else:
        files = generator.generate_full_package(matches, profile, output, project_name)

    # Show what will be generated
    console.print("\n[cyan]Files to generate:[/cyan]")
    for filename, content in files.items():
        lines = content.count("\n") + 1
        console.print(f"  📄 {filename} ({lines} lines)")

    if dry_run:
        console.print("\n[yellow]Dry run - no files written[/yellow]")

        # Show preview of AGENTS.md
        console.print("\n[cyan]Preview of AGENTS.md:[/cyan]")
        preview_lines = files.get("AGENTS.md", "").split("\n")[:30]
        for line in preview_lines:
            console.print(f"  [dim]{line}[/dim]")
        if len(files.get("AGENTS.md", "").split("\n")) > 30:
            console.print("  [dim]...[/dim]")
        return

    # Write files
    written = generator.write_files(files, output, overwrite)

    if written:
        console.print(
            Panel(
                f"[green]✅ Success![/green]\n\n"
                f"Generated {len(written)} files:\n" + "\n".join(f"  • {f}" for f in written),
                title="Generation Complete",
            )
        )
    else:
        console.print(
            "[yellow]No files written. Files may already exist. "
            "Use --overwrite to replace.[/yellow]"
        )


@cli.command()
@click.option(
    "--vibe-tools",
    type=click.Path(exists=True),
    default=None,
    help="Path to vibe-tools directory",
)
@click.option("--clear/--no-clear", default=False, help="Clear existing collection first")
@click.option("--verbose/--no-verbose", default=True, help="Print progress messages")
def ingest(vibe_tools: str | None, clear: bool, verbose: bool):
    """📥 Ingest all agents into Chroma for discovery."""
    from agent_discovery.collector import AgentCollector
    from agent_discovery.ingester import AgentIngester

    # Find vibe-tools root
    if vibe_tools:
        root = Path(vibe_tools)
    else:
        # Try to find it relative to current directory or common locations
        candidates = [
            Path.cwd(),
            Path.cwd().parent,
            Path.home() / "Development/Tools/vibe-tools",
            Path("/home/ob/Development/Tools/vibe-tools"),
        ]
        root = None
        for candidate in candidates:
            if (candidate / "ghc_tools/agents").exists():
                root = candidate
                break

        if not root:
            console.print(
                "[red]❌ Could not find vibe-tools directory. "
                "Use --vibe-tools to specify the path.[/red]"
            )
            raise SystemExit(1)

    console.print(f"[blue]📂 Using vibe-tools root: {root}[/blue]")

    # Collect agents
    console.print("\n[yellow]Step 1: Collecting agents...[/yellow]")
    collector = AgentCollector(str(root))
    agents = collector.collect_all(verbose=verbose)

    # Deduplicate
    agents = collector.deduplicate(agents)
    console.print(f"[green]✓ {len(agents)} unique agents collected[/green]")

    # Print statistics
    stats = collector.get_statistics(agents)
    table = Table(title="Collection Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="green")

    table.add_row("Total Agents", str(stats["total"]))
    for agent_type, count in sorted(stats["by_type"].items()):
        table.add_row(f"  {agent_type}s", str(count))

    console.print(table)

    # Ingest to Chroma
    console.print("\n[yellow]Step 2: Ingesting to Chroma...[/yellow]")
    ingester = AgentIngester()

    if clear:
        ingester.clear_collection(verbose=verbose)

    agents_processed, chunks = ingester.ingest(agents, verbose=verbose)

    console.print(
        Panel(
            f"[green]✅ Success![/green]\n\n"
            f"Agents processed: {agents_processed}\n"
            f"Chunks created: {chunks}",
            title="Ingestion Complete",
        )
    )


@cli.command()
@click.option("--path", type=click.Path(exists=True), default=".", help="Path to codebase")
@click.option("--interactive/--no-interactive", default=True, help="Use interactive mode")
@click.option("--results", "-n", default=5, help="Number of results to show")
@click.option(
    "--generate-output", "-g", type=click.Path(), help="Generate AGENTS.md to this directory"
)
@click.option(
    "--min-score",
    default=0.35,
    type=float,
    help="Minimum match score (0-1, default 0.35)",
)
@click.option(
    "--subject-top",
    multiple=True,
    help="Cap results per subject (e.g., --subject-top data-science=2)",
)
def discover(
    path: str,
    interactive: bool,
    results: int,
    generate_output: str | None,
    min_score: float | None,
    subject_top: tuple[str, ...],
):
    """🔍 Discover agents for your codebase."""
    from agent_discovery.discovery import DiscoveryEngine
    from agent_discovery.questions import QuestionGenerator

    engine = DiscoveryEngine()
    question_gen = QuestionGenerator()

    console.print(
        Panel(
            "[bold blue]🔍 Agent Discovery System[/bold blue]\n\n"
            "I'll help you find the perfect agents for your codebase.",
            title="Welcome",
        )
    )

    # Analyze codebase
    console.print(f"\n[yellow]Analyzing codebase at: {path}[/yellow]")
    try:
        profile = engine.analyze_codebase(path)
        console.print("[green]✓ Analysis complete[/green]")

        if profile.languages:
            console.print(f"  Languages: {', '.join(profile.languages)}")
        if profile.frameworks:
            console.print(f"  Frameworks: {', '.join(profile.frameworks)}")
        if profile.patterns:
            console.print(f"  Patterns: {', '.join(profile.patterns)}")
    except Exception as e:
        console.print(f"[yellow]⚠️ Could not analyze codebase: {e}[/yellow]")
        profile = None

    answers = {}

    if interactive:
        try:
            import questionary
        except ImportError:
            console.print("[red]questionary not installed. Using non-interactive mode.[/red]")
            interactive = False

    if interactive:
        import questionary

        # Get relevant questions
        questions = (
            question_gen.get_questions_for_profile(profile)
            if profile
            else question_gen.get_all_questions()
        )

        console.print("\n[cyan]Please answer a few questions:[/cyan]\n")

        for q in questions:
            if q.question_type == "single":
                choices = [opt["label"] for opt in q.options]
                values = [opt["value"] for opt in q.options]
                answer = questionary.select(
                    q.text,
                    choices=choices,
                ).ask()
                if answer:
                    idx = choices.index(answer)
                    answers[q.id] = values[idx]

            elif q.question_type == "multi":
                choices = [
                    questionary.Choice(opt["label"], value=opt["value"]) for opt in q.options
                ]
                answer = questionary.checkbox(
                    q.text,
                    choices=choices,
                ).ask()
                if answer:
                    answers[q.id] = answer

            elif q.question_type == "text":
                answer = questionary.text(q.text).ask()
                if answer:
                    answers[q.id] = answer

    # Build search criteria
    criteria = question_gen.process_answers(answers, profile)

    # Perform discovery
    console.print("\n[yellow]Searching for matching agents...[/yellow]")
    matches = engine.discover(
        criteria,
        n_results=results,
        min_score=min_score,
        subject_top_n=_parse_subject_top(subject_top),
    )

    if not matches:
        console.print("[red]No matching agents found. Try broadening your criteria.[/red]")
        return

    # Display results
    console.print(f"\n[green]🎯 Found {len(matches)} matching agents:[/green]\n")

    for i, match in enumerate(matches, 1):
        score_pct = int(match.score * 100)
        score_color = "green" if score_pct >= 80 else "yellow" if score_pct >= 60 else "red"

        console.print(
            f"[bold]{i}. {match.agent.name}[/bold] "
            f"[{score_color}](⭐ {score_pct}% match)[/{score_color}]"
        )
        console.print(f"   [dim]{match.agent.description or 'No description'}[/dim]")
        if match.match_reasons:
            console.print(f"   [cyan]Why: {', '.join(match.match_reasons)}[/cyan]")
        agent_type = match.agent.agent_type.value
        category = match.agent.category.value
        console.print(f"   [dim]Type: {agent_type} | Category: {category}[/dim]")
        console.print()

    # Generate output if requested
    if generate_output and matches:
        from agent_discovery.generator import OutputGenerator

        generator = OutputGenerator()
        project_name = Path(path).resolve().name if path != "." else Path.cwd().name

        console.print("[yellow]Generating configuration files...[/yellow]")
        files = generator.generate_full_package(matches, profile, generate_output, project_name)
        written = generator.write_files(files, generate_output, overwrite=False)

        if written:
            console.print(f"[green]✓ Generated {len(written)} files in {generate_output}[/green]")
            for f in written:
                console.print(f"  📄 {f}")
        else:
            console.print(
                "[yellow]Files already exist. Use 'generate --overwrite' to replace.[/yellow]"
            )


@cli.command()
@click.argument("query")
@click.option("--results", "-n", default=5, help="Number of results")
@click.option(
    "--min-score",
    default=0.35,
    type=float,
    help="Minimum match score (0-1, default 0.35)",
)
@click.option(
    "--subject-top",
    multiple=True,
    help="Cap results per subject (e.g., --subject-top database=2)",
)
def search(query: str, results: int, min_score: float | None, subject_top: tuple[str, ...]):
    """🔎 Quick search for agents by keyword."""
    from agent_discovery.discovery import DiscoveryEngine

    engine = DiscoveryEngine()

    console.print(f"[yellow]Searching for: {query}[/yellow]\n")

    matches = engine.quick_search(
        query,
        n_results=results,
        min_score=min_score,
        subject_top_n=_parse_subject_top(subject_top),
    )

    if not matches:
        console.print("[red]No matching agents found.[/red]")
        return

    for i, match in enumerate(matches, 1):
        score_pct = int(match.score * 100)
        console.print(f"[bold]{i}. {match.agent.name}[/bold] (⭐ {score_pct}%)")
        console.print(f"   {match.agent.description or 'No description'}")
        console.print(f"   [dim]Type: {match.agent.agent_type.value}[/dim]")
        console.print()


@cli.command("list")
@click.option(
    "--type", "-t", "agent_type", help="Filter by type (agent, prompt, instruction, chatmode)"
)
@click.option("--category", "-c", help="Filter by category")
@click.option("--limit", "-l", default=20, help="Number of results")
def list_agents(agent_type: str | None, category: str | None, limit: int):
    """📋 List all available agents."""
    from agent_discovery.ingester import AgentRetriever

    retriever = AgentRetriever()

    if agent_type:
        results = retriever.search_by_type(agent_type, n_results=limit)
    elif category:
        results = retriever.search_by_category(category, n_results=limit)
    else:
        results = retriever.get_all_agents(limit=limit)

    if not results:
        console.print("[yellow]No agents found. Run 'agent-discover ingest' first.[/yellow]")
        return

    table = Table(title=f"Agents ({len(results)} found)")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Category", style="yellow")
    table.add_column("Description", style="dim")

    for result in results:
        meta = result["metadata"]
        table.add_row(
            meta.get("agent_name", "unknown"),
            meta.get("agent_type", "?"),
            meta.get("category", "?"),
            (meta.get("description", "") or "")[:50],
        )

    console.print(table)


@cli.command()
def stats():
    """📊 Show collection statistics."""
    from agent_discovery.ingester import AgentIngester, AgentRetriever

    ingester = AgentIngester()
    retriever = AgentRetriever()

    stats = ingester.get_stats()

    console.print(
        Panel(
            f"[bold]Collection:[/bold] {stats.get('collection_name', 'unknown')}\n"
            f"[bold]Total Chunks:[/bold] {stats.get('total_chunks', 0)}",
            title="📊 Collection Statistics",
        )
    )

    # Count by type
    console.print("\n[cyan]Agents by Type:[/cyan]")
    for agent_type in ["agent", "prompt", "instruction", "chatmode"]:
        results = retriever.search_by_type(agent_type, n_results=500)
        console.print(f"  {agent_type}s: {len(results)}")

    # Count by category
    console.print("\n[cyan]Agents by Category:[/cyan]")
    categories = [
        "frontend",
        "backend",
        "fullstack",
        "architecture",
        "testing",
        "ai_ml",
        "devops",
        "security",
        "quality",
        "database",
        "planning",
        "documentation",
        "general",
    ]
    for cat in categories:
        results = retriever.search_by_category(cat, n_results=500)
        if results:
            console.print(f"  {cat}: {len(results)}")


@cli.command()
@click.option("--subject", "-s", help="Filter by subject (e.g., security, testing, infra)")
@click.option("--limit", "-l", default=10, help="Top N agents to show")
def leaderboard(subject: str | None, limit: int):
    """🏆 Show top agents per subject for building ultimate agents."""
    from agent_discovery.ingester import AgentRetriever

    retriever = AgentRetriever()

    if subject:
        console.print(f"[cyan]🏆 Top {limit} agents for subject: {subject}[/cyan]\n")
        # Query agents where subjects field contains the subject
        results = retriever.search(
            query=subject,
            n_results=limit * 2,
        )
        # Filter by subjects metadata
        filtered = [r for r in results if subject in r["metadata"].get("subjects", "").split(",")][
            :limit
        ]
        if not filtered:
            # Fallback: use category if subjects not populated
            filtered = retriever.search_by_category(subject, n_results=limit)
    else:
        console.print("[cyan]🏆 Top agents across all subjects[/cyan]\n")
        filtered = retriever.get_all_agents(limit=limit)

    if not filtered:
        console.print("[yellow]No agents found. Run 'agent-discover ingest' first.[/yellow]")
        return

    table = Table(title=f"Leaderboard ({len(filtered)} agents)")
    table.add_column("#", style="bold")
    table.add_column("Agent", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Category", style="yellow")
    table.add_column("Subjects", style="magenta")
    table.add_column("Score", style="bold green")

    for i, result in enumerate(filtered, 1):
        meta = result.get("metadata", result)
        score = result.get("score", "-")
        if isinstance(score, float):
            score = f"{int(score * 100)}%"
        table.add_row(
            str(i),
            meta.get("agent_name", "unknown"),
            meta.get("agent_type", "?"),
            meta.get("category", "?"),
            meta.get("subjects", "")[:30],
            str(score),
        )

    console.print(table)


@cli.command("ultimate")
@click.option(
    "--subject", "-s", required=True, help="Subject for ultimate agent (e.g., security, testing)"
)
@click.option("--top", "-t", default=5, help="Number of top agents to combine")
@click.option("--output", "-o", type=click.Path(), default=".", help="Output directory")
@click.option("--name", help="Name for the ultimate agent (default: ultimate-{subject})")
@click.option("--dry-run", is_flag=True, help="Preview without writing files")
@click.option(
    "--min-score",
    default=0.35,
    type=float,
    help="Minimum match score (0-1, default 0.35)",
)
@click.option(
    "--subject-top",
    multiple=True,
    help="Cap results per subject (e.g., --subject-top data-science=2)",
)
def ultimate_agent(
    subject: str,
    top: int,
    output: str,
    name: str | None,
    dry_run: bool,
    min_score: float | None,
    subject_top: tuple[str, ...],
):
    """🦾 Generate an ultimate composite agent for a subject.

    Combines the top-ranked agents, prompts, and instructions for a subject
    into a single deployable configuration.

    Examples:
        agent-discover ultimate --subject security
        agent-discover ultimate --subject testing --top 7 --output ./agents
    """
    from pathlib import Path as P

    from agent_discovery.agent_synthesizer import AgentSynthesizer
    from agent_discovery.discovery import DiscoveryEngine

    engine = DiscoveryEngine()
    synthesizer = AgentSynthesizer(base_path="./")
    agent_name = name or f"ultimate-{subject}"

    console.print(
        Panel(
            f"[bold blue]🦾 Ultimate Agent Generator[/bold blue]\n\n"
            f"Building: [cyan]{agent_name}[/cyan]\n"
            f"Subject: [yellow]{subject}[/yellow]\n"
            f"Top agents: {top}",
            title="Ultimate Agent",
        )
    )

    # Gather top agents for the subject
    console.print("\n[yellow]Step 1: Finding top agents...[/yellow]")

    # Improved search: use enhanced keywords and filter for agents only
    from agent_discovery.subject_search import enhance_search_query

    enhanced_query = enhance_search_query(subject)
    effective_min_score = min_score if min_score is not None else 0.40

    console.print(f"  [dim]Searching for: {enhanced_query}[/dim]")

    matches = engine.quick_search(
        query=enhanced_query,
        n_results=top * 10,  # Get even more candidates for better filtering
        min_score=effective_min_score,
        subject_top_n=_parse_subject_top(subject_top),
    )

    # Filter to only agents (not prompts/instructions/chatmodes)
    agent_matches = [m for m in matches if m.agent.agent_type.value == "agent"]

    if not agent_matches:
        # Fall back to all matches if no pure agents found
        agent_matches = matches[:top]

    if not agent_matches:
        console.print("[red]No agents found for this subject.[/red]")
        return

    console.print(f"[green]✓ Found {len(agent_matches)} matching agents[/green]")
    for m in agent_matches[:top]:
        console.print(f"  • {m.agent.name} ({int(m.score * 100)}% match)")

    # Synthesize ultimate agent from top matches
    console.print("\n[yellow]Step 2: Synthesizing agent from specialists...[/yellow]")
    content = synthesizer.synthesize(
        subject=subject,
        matches=agent_matches,
        top_n=top,
    )

    if dry_run:
        console.print("\n[cyan]Preview (dry-run):[/cyan]")
        for line in content.split("\n")[:50]:
            console.print(f"  [dim]{line}[/dim]")
        if len(content.split("\n")) > 50:
            console.print("  [dim]...[/dim]")
        return

    # Write file
    output_path = P(output) / f"{agent_name}.agent.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")

    console.print(
        Panel(
            f"[green]✅ Success![/green]\n\n"
            f"Generated: [cyan]{output_path}[/cyan]\n"
            f"Specialists synthesized: {min(len(agent_matches), top)}",
            title="Ultimate Agent Created",
        )
    )


@cli.command()
@click.argument("domain")
@click.option(
    "--type",
    "-t",
    "agent_type",
    type=click.Choice(["agent", "instruction", "prompt", "chatmode"]),
    default="agent",
    help="Type of agent to create",
)
@click.option("--name", "-n", help="Custom name for the agent (default: derived from domain)")
@click.option("--output", "-o", type=click.Path(), help="Output directory")
@click.option("--analyze-only", is_flag=True, help="Only show analysis, don't generate")
@click.option("--prompt-only", is_flag=True, help="Generate LLM prompt instead of template")
@click.option("--samples", default=10, help="Number of samples to analyze")
def create(
    domain: str,
    agent_type: str,
    name: str | None,
    output: str | None,
    analyze_only: bool,
    prompt_only: bool,
    samples: int,
):
    """🔨 Create a new agent by learning from existing ones in Chroma.

    Analyzes patterns from existing agents and generates a new agent
    for the specified domain.

    Examples:
        agent-discover create "kubernetes deployment"
        agent-discover create "react testing" --type instruction
        agent-discover create "database optimization" --analyze-only
        agent-discover create "api validation" --prompt-only
    """
    from agent_discovery.creator import AgentCreator

    console.print(
        Panel(
            f"[bold blue]🔨 Agent Creator[/bold blue]\n\n"
            f"Creating {agent_type} for: [cyan]{domain}[/cyan]",
            title="Create",
        )
    )

    creator = AgentCreator()

    # Step 1: Analyze patterns
    console.print(f"\n[yellow]Step 1: Analyzing patterns from {samples} samples...[/yellow]")

    try:
        patterns = creator.analyze_patterns(domain, n_samples=samples)
        console.print("[green]✓ Pattern analysis complete[/green]")
        console.print(f"  Common sections: {', '.join(patterns.common_sections[:5])}")
        console.print(f"  Frontmatter fields: {', '.join(patterns.frontmatter_fields)}")
        console.print(f"  Avg length: {patterns.avg_length} chars")
    except Exception as e:
        console.print(f"[red]Error analyzing patterns: {e}[/red]")
        console.print("[dim]Make sure agents are ingested: agent-discover ingest[/dim]")
        return

    # Step 2: Get domain context
    console.print("\n[yellow]Step 2: Getting domain context...[/yellow]")

    context = creator.get_domain_context(domain, n_results=5)
    console.print(f"[green]✓ Found {context['total_found']} related agents[/green]")

    table = Table(title="Related Agents")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Relevance", style="green")
    table.add_column("Description", style="dim", max_width=40)

    for agent in context["related_agents"]:
        table.add_row(
            agent["name"],
            agent["type"],
            f"{agent['relevance']}%",
            (
                (agent["description"][:37] + "...")
                if len(agent["description"]) > 40
                else agent["description"]
            ),
        )

    console.print(table)

    if analyze_only:
        # Step 3a: Show vocabulary
        console.print("\n[yellow]Step 3: Domain vocabulary:[/yellow]")
        vocabulary = creator.extract_vocabulary(domain, n_samples=samples)
        vocab_list = sorted(list(vocabulary))[:30]
        console.print(f"  {', '.join(vocab_list)}")
        return

    # Step 3: Generate content
    console.print(f"\n[yellow]Step 3: Generating {agent_type}...[/yellow]")

    if prompt_only:
        # Generate LLM prompt
        prompt = creator.generate_agent_prompt(domain, agent_type)
        console.print("\n[cyan]LLM Prompt for Agent Generation:[/cyan]")
        console.print(Panel(prompt, title="Copy this prompt"))
        return

    # Generate template
    agent_name = name or domain.lower().replace(" ", "-")
    content = creator.generate_agent_template(domain, agent_type, agent_name)

    # Step 4: Save or display
    if output:
        output_path = creator.save_agent(content, agent_name, agent_type, output)
        console.print(
            Panel(
                f"[green]✅ Success![/green]\n\n"
                f"Created: [cyan]{output_path}[/cyan]\n"
                f"Type: {agent_type}\n"
                f"Based on: {context['total_found']} related agents",
                title="Agent Created",
            )
        )
    else:
        console.print("\n[cyan]Generated Template:[/cyan]")
        console.print(Panel(content, title=f"{agent_name}.{agent_type}.md"))
        console.print("\n[dim]Use --output to save to a file[/dim]")


@cli.command("analyze-all")
@click.option(
    "--collection-only",
    is_flag=True,
    help="Discover agents only (skip execution and analysis)",
)
@click.option(
    "--enable-execution",
    is_flag=True,
    help="Execute agents with real code (default: mock execution)",
)
@click.option(
    "--source",
    type=click.Path(exists=True),
    help="Specific vibe-tools source directory to analyze",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show detailed progress output",
)
def analyze_all(collection_only: bool, enable_execution: bool, source: str | None, verbose: bool):
    """🚀 Run full agent learning pipeline with discovery enhancement.

    Executes the complete 5-phase pipeline:
    1. Collect agents from vibe-tools
    2. Execute agents with metric capture
    3. Aggregate performance metrics
    4. Extract success/failure patterns
    5. Enhance agent discovery with historical context

    Examples:
        agent-discover analyze-all                                    # Full pipeline
        agent-discover analyze-all --collection-only                  # Discover only
        agent-discover analyze-all --enable-execution                 # Real execution
        agent-discover analyze-all --source ~/Development/vibe-tools  # Custom source
        agent-discover analyze-all -v                                 # Verbose output
    """
    from agent_discovery.pipeline import AgentPipeline, PipelineConfig

    console.print(
        Panel(
            "[bold blue]🚀 Agent Learning Pipeline[/bold blue]\n\n"
            "[dim]Phase 1-5: Collect → Execute → Aggregate → Extract → Enhance[/dim]",
            title="Analyze All Agents",
        )
    )

    # Determine vibe-tools root directory
    if source:
        vibe_tools_root = Path(source)
    else:
        # Default to parent directories looking for vibe-tools structure
        current_dir = Path.cwd()
        vibe_tools_root = None

        # Check if we're already in a vibe-tools directory
        if current_dir.parent.name == "vibe-tools" or "vibe-tools" in str(current_dir):
            vibe_tools_root = current_dir
        else:
            # Look for vibe-tools in parent directories
            for parent in current_dir.parents:
                if parent.name == "vibe-tools" or (parent / ".github" / "agents").exists():
                    vibe_tools_root = parent
                    break

        if not vibe_tools_root:
            # Default to home directory vibe-tools
            vibe_tools_root = Path.home() / "Development" / "Tools" / "vibe-tools"

    # Configure pipeline
    config = PipelineConfig(
        enable_execution=enable_execution,
        verbose=verbose,
    )

    if verbose:
        console.print(
            f"\n[cyan]Configuration:[/cyan]\n"
            f"  Collection Only: {collection_only}\n"
            f"  Enable Execution: {enable_execution}\n"
            f"  Vibe-tools Root: {vibe_tools_root}\n"
            f"  Verbose: {verbose}"
        )

    # Run pipeline
    console.print("\n[yellow]Starting pipeline execution...[/yellow]")
    start_time = time.time()

    try:
        pipeline = AgentPipeline(vibe_tools_root=vibe_tools_root, config=config)

        if collection_only:
            # Phase 1 only: Collect agents
            if verbose:
                console.print("[cyan]→ Phase 1: Collecting agents...[/cyan]")

            agents = pipeline._collect_agents()

            console.print(
                Panel(
                    f"[green]✓ Phase 1 Complete[/green]\n\n"
                    f"Agents discovered: [cyan]{len(agents)}[/cyan]",
                    title="Collection Results",
                )
            )

            # Display agents in a table
            if agents:
                table = Table(title="Discovered Agents")
                table.add_column("Name", style="cyan")
                table.add_column("Type", style="magenta")
                table.add_column("Category", style="green")
                table.add_column("Description", style="dim", max_width=40)

                for agent in agents[:20]:  # Show first 20
                    desc = (
                        (agent.description[:37] + "...")
                        if agent.description and len(agent.description) > 40
                        else (agent.description or "N/A")
                    )
                    table.add_row(
                        agent.name,
                        agent.agent_type.value,
                        agent.category.value if agent.category else "N/A",
                        desc,
                    )

                console.print(table)

                if len(agents) > 20:
                    console.print(f"\n[dim]... and {len(agents) - 20} more agents[/dim]")
        else:
            # Full pipeline: Collect → Execute → Aggregate → Extract → Enhance
            result = pipeline.run_full_pipeline()

            elapsed = time.time() - start_time

            # Display results
            console.print(
                Panel(
                    result.summary(),
                    title="Pipeline Results",
                )
            )

            # Display performance metrics if available
            if result.metrics:
                console.print("\n[cyan]Performance Metrics:[/cyan]")
                metrics_table = Table()
                metrics_table.add_column("Metric", style="cyan")
                metrics_table.add_column("Value", style="green")

                for metric_name, metric_value in result.metrics.items():
                    if isinstance(metric_value, (int, float)):
                        if isinstance(metric_value, float):
                            metrics_table.add_row(metric_name, f"{metric_value:.2f}")
                        else:
                            metrics_table.add_row(metric_name, str(metric_value))

                console.print(metrics_table)

            # Display warnings if any
            if result.warnings:
                console.print("\n[yellow]Warnings:[/yellow]")
                for warning in result.warnings:
                    console.print(f"  [yellow]⚠[/yellow] {warning}")

            # Display errors if any
            if result.errors:
                console.print("\n[red]Errors:[/red]")
                for error in result.errors:
                    console.print(f"  [red]✗[/red] {error}")

            # Summary stats
            console.print(
                Panel(
                    f"[green]✅ Pipeline Execution Complete[/green]\n\n"
                    f"Total time: [cyan]{elapsed:.2f}s[/cyan]\n"
                    f"Agents processed: [cyan]{result.agents_collected}[/cyan]\n"
                    f"Execution success rate: [cyan]{result.success_rate:.1%}[/cyan]",
                    title="Execution Summary",
                )
            )

    except Exception as e:
        elapsed = time.time() - start_time
        console.print(
            Panel(
                f"[red]✗ Pipeline execution failed[/red]\n\n"
                f"Error: {str(e)}\n"
                f"Time elapsed: {elapsed:.2f}s",
                title="Error",
            )
        )
        if verbose:
            import traceback

            console.print(f"\n[dim]{traceback.format_exc()}[/dim]")


if __name__ == "__main__":
    cli()
