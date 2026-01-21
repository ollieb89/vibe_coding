"""Document shape analysis - structure metrics per category."""

import json
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import NamedTuple

from corpus_analyzer.core.database import CorpusDatabase
from corpus_analyzer.core.models import DocumentCategory


class ShapeReport(NamedTuple):
    """Shape analysis report for a document category."""

    category: str
    doc_count: int
    heading_frequency: dict[str, int]
    heading_depth_distribution: dict[int, int]
    avg_headings_per_doc: float
    avg_code_blocks_per_doc: float
    avg_links_per_doc: float
    code_density: float  # % of docs with code
    size_p50: int
    size_p90: int
    token_p50: int
    token_p90: int
    common_section_order: list[str]
    recommended_sections: list[str]


def analyze_category(db: CorpusDatabase, category: DocumentCategory) -> ShapeReport:
    """Generate shape report for a document category."""
    docs = list(db.get_documents(category=category))

    if not docs:
        return ShapeReport(
            category=category.value,
            doc_count=0,
            heading_frequency={},
            heading_depth_distribution={},
            avg_headings_per_doc=0.0,
            avg_code_blocks_per_doc=0.0,
            avg_links_per_doc=0.0,
            code_density=0.0,
            size_p50=0,
            size_p90=0,
            token_p50=0,
            token_p90=0,
            common_section_order=[],
            recommended_sections=[],
        )

    # Heading analysis
    all_headings: Counter[str] = Counter()
    depth_dist: Counter[int] = Counter()
    section_orders: list[list[str]] = []

    headings_per_doc: list[int] = []
    code_blocks_per_doc: list[int] = []
    links_per_doc: list[int] = []
    docs_with_code = 0
    sizes: list[int] = []
    tokens: list[int] = []

    for doc in docs:
        # Count headings
        heading_texts = [h.text.lower() for h in doc.headings]
        all_headings.update(heading_texts)
        section_orders.append([h.text for h in doc.headings if h.level <= 2])

        # Depth distribution
        for h in doc.headings:
            depth_dist[h.level] += 1

        headings_per_doc.append(len(doc.headings))
        code_blocks_per_doc.append(len(doc.code_blocks))
        links_per_doc.append(len(doc.links))

        if doc.code_blocks:
            docs_with_code += 1

        sizes.append(doc.size_bytes)
        tokens.append(doc.token_estimate)

    # Calculate percentiles
    sizes_sorted = sorted(sizes)
    tokens_sorted = sorted(tokens)

    def percentile(data: list[int], p: float) -> int:
        if not data:
            return 0
        idx = int(len(data) * p)
        return data[min(idx, len(data) - 1)]

    # Find common section order
    common_sections = [h for h, _ in all_headings.most_common(10)]

    # Recommended sections: appear in >60% of docs
    threshold = len(docs) * 0.6
    recommended = [h for h, count in all_headings.items() if count >= threshold]

    return ShapeReport(
        category=category.value,
        doc_count=len(docs),
        heading_frequency=dict(all_headings.most_common(20)),
        heading_depth_distribution=dict(depth_dist),
        avg_headings_per_doc=mean(headings_per_doc) if headings_per_doc else 0.0,
        avg_code_blocks_per_doc=mean(code_blocks_per_doc) if code_blocks_per_doc else 0.0,
        avg_links_per_doc=mean(links_per_doc) if links_per_doc else 0.0,
        code_density=docs_with_code / len(docs) if docs else 0.0,
        size_p50=percentile(sizes_sorted, 0.5),
        size_p90=percentile(sizes_sorted, 0.9),
        token_p50=percentile(tokens_sorted, 0.5),
        token_p90=percentile(tokens_sorted, 0.9),
        common_section_order=common_sections,
        recommended_sections=recommended,
    )


def generate_shape_reports(db: CorpusDatabase, output_dir: Path) -> list[Path]:
    """Generate shape reports for all categories."""
    reports: list[Path] = []

    for category_name in db.get_categories():
        try:
            category = DocumentCategory(category_name)
        except ValueError:
            continue

        report = analyze_category(db, category)

        # Create category output directory
        cat_dir = output_dir / category_name
        cat_dir.mkdir(parents=True, exist_ok=True)

        # Write shape.md
        shape_md = cat_dir / "shape.md"
        shape_md.write_text(_format_shape_report_md(report))
        reports.append(shape_md)

        # Write heading_frequency.csv
        freq_csv = cat_dir / "heading_frequency.csv"
        freq_csv.write_text(_format_heading_frequency_csv(report))
        reports.append(freq_csv)

        # Write recommended_schema.json
        schema_json = cat_dir / "recommended_schema.json"
        schema_json.write_text(json.dumps(_generate_recommended_schema(report), indent=2))
        reports.append(schema_json)

    return reports


def _format_shape_report_md(report: ShapeReport) -> str:
    """Format shape report as markdown."""
    return f"""# Shape Report: {report.category}

## Overview

- **Documents**: {report.doc_count}
- **Avg headings/doc**: {report.avg_headings_per_doc:.1f}
- **Avg code blocks/doc**: {report.avg_code_blocks_per_doc:.1f}
- **Avg links/doc**: {report.avg_links_per_doc:.1f}
- **Code density**: {report.code_density:.0%}

## Size Metrics

| Metric | P50 | P90 |
|--------|-----|-----|
| Size (bytes) | {report.size_p50:,} | {report.size_p90:,} |
| Tokens (est.) | {report.token_p50:,} | {report.token_p90:,} |

## Heading Depth Distribution

| Level | Count |
|-------|-------|
{chr(10).join(f"| H{level} | {count} |" for level, count in sorted(report.heading_depth_distribution.items()))}

## Most Common Headings

{chr(10).join(f"- {h} ({c})" for h, c in report.heading_frequency.items())}

## Recommended Sections

These headings appear in >60% of documents:

{chr(10).join(f"- {h}" for h in report.recommended_sections) or "- (none)"}

## Common Section Order

{chr(10).join(f"{i+1}. {h}" for i, h in enumerate(report.common_section_order[:10]))}
"""


def _format_heading_frequency_csv(report: ShapeReport) -> str:
    """Format heading frequency as CSV."""
    lines = ["heading,count"]
    for heading, count in report.heading_frequency.items():
        # Escape commas and quotes
        safe_heading = heading.replace('"', '""')
        if "," in heading:
            safe_heading = f'"{safe_heading}"'
        lines.append(f"{safe_heading},{count}")
    return "\n".join(lines)


def _generate_recommended_schema(report: ShapeReport) -> dict:
    """Generate recommended schema from analysis."""
    return {
        "category": report.category,
        "doc_count": report.doc_count,
        "sections": {
            "required": report.recommended_sections[:5],
            "optional": [
                h for h in report.common_section_order
                if h not in report.recommended_sections
            ][:5],
        },
        "metrics": {
            "code_density": report.code_density,
            "avg_headings": report.avg_headings_per_doc,
            "token_p50": report.token_p50,
            "token_p90": report.token_p90,
        },
    }
