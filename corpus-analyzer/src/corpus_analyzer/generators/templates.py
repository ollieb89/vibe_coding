"""Template generation from shape analysis."""

from pathlib import Path

from corpus_analyzer.analyzers.shape import analyze_category
from corpus_analyzer.core.database import CorpusDatabase
from corpus_analyzer.core.models import DocumentCategory


TEMPLATES = ['howto', 'runbook', 'persona', 'reference', 'tutorial', 'spec']

TEMPLATE_CONTRACTS = {
    'howto': """<!--
TEMPLATE CONTRACT
Required: [Role Definition, Context, Requirements, Instructions, Output Format]
Optional: [Reference Examples]
Never Include: [Generic marketing intros, Unrelated resources]
-->""",
    'runbook': """<!--
TEMPLATE CONTRACT
Required: [Description, Configuration, Phases (Action/Prompt/Output/Context), Success Criteria]
Optional: [Coordination Protocols]
Never Include: [Ambiguous steps, Non-actionable philosophy]
-->""",
    'persona': """<!--
TEMPLATE CONTRACT
Required: [Role name, Context, Capabilities, Strategies/Implementation, Arguments]
Optional: [Reference Workflows]
Never Include: [First-person biography without technical substance]
-->""",
    'reference': """<!--
TEMPLATE CONTRACT
Required: [Description, Configuration Options, Content Sections, Output Format]
Optional: [Success Criteria]
Never Include: [Tutorial-style steps unless describing a workflow]
-->""",
    'tutorial': """<!--
TEMPLATE CONTRACT
Required: [Role, Core Expertise, Process, Structure (Opening/Progressive/Closing)]
Optional: [Quality Checklist, Writing Principles]
Never Include: [assumed prior knowledge without prerequisites]
-->""",
    'spec': """<!--
TEMPLATE CONTRACT
Required: [Context, Requirements, Instructions (Steps + Code), Output Format]
Optional: [Best Practices]
Never Include: [Vague requirements]
-->"""
}


def generate_from_analysis(db: CorpusDatabase, output_dir: Path) -> list[Path]:
    """Generate templates for each document category based on analysis."""
    templates: list[Path] = []

    for category_name in db.get_categories():
        try:
            category = DocumentCategory(category_name)
        except ValueError:
            continue

        report = analyze_category(db, category)
        if report.doc_count == 0:
            continue

        # Generate markdown template
        template_path = output_dir / f"{category_name}.md"
        template_path.write_text(_generate_template_md(report.category, report.recommended_sections, report.common_section_order))
        templates.append(template_path)

        # Generate lint rules
        lint_path = output_dir / f"{category_name}.lint.yml"
        lint_path.write_text(_generate_lint_rules(report.category, report.recommended_sections))
        templates.append(lint_path)

    return templates


def _generate_template_md(category: str, required: list[str], optional: list[str]) -> str:
    """Generate a markdown template from analysis."""
    lines = [
        "---",
        f"type: {category}",
        "---",
        "",
        f"# {{{{ title }}}}",
        "",
    ]

    # Add required sections
    if required:
        lines.append("<!-- Required sections -->")
        for section in required[:5]:
            # Normalize to title case
            section_title = section.title() if section.islower() else section
            lines.extend([
                f"## {section_title}",
                "",
                f"<!-- TODO: Add {section_title.lower()} content -->",
                "",
            ])

    # Add optional sections as comments
    remaining_optional = [s for s in optional if s.lower() not in [r.lower() for r in required]]
    if remaining_optional:
        lines.append("<!-- Optional sections (uncomment as needed)")
        for section in remaining_optional[:5]:
            section_title = section.title() if section.islower() else section
            lines.extend([
                f"## {section_title}",
                "",
            ])
        lines.append("-->")
        lines.append("")

    return "\n".join(lines)


def _generate_lint_rules(category: str, required: list[str]) -> str:
    """Generate linting rules for the template."""
    rules = [
        f"# Lint rules for {category} documents",
        "",
        "rules:",
        f"  category: {category}",
        "",
        "  # Required headings",
        "  required_headings:",
    ]

    for section in required[:5]:
        rules.append(f"    - \"{section}\"")

    rules.extend([
        "",
        "  # Structure constraints",
        "  max_heading_depth: 4",
        "  require_h1: true",
        "",
        "  # Quality checks",
        "  require_frontmatter: true",
        "  min_content_length: 100",
    ])

    return "\n".join(rules)
