"""Result exporter for multi-format output of execution analysis.

This module provides export functionality for execution results in multiple
formats (JSON, CSV, TEXT, REPORT, HTML). It combines EnhancedResult,
PerformancePrediction, and CodeRecommendation into human and machine
readable outputs suitable for dashboards, reports, and data analysis.

Features:
- Multiple export formats (JSON, CSV, TEXT, REPORT, HTML)
- Single and batch result export
- Safe handling of None/missing values
- Timestamp generation for all exports
- Comprehensive metadata inclusion
"""

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from io import StringIO
from typing import Any


class ExportFormat(Enum):
    """Supported export formats."""

    JSON = "json"
    """JSON format with nested structure and full metadata."""

    CSV = "csv"
    """CSV format for spreadsheet import."""

    TEXT = "text"
    """Plain text format for terminal/email display."""

    REPORT = "report"
    """Markdown formatted report for documentation."""

    HTML = "html"
    """HTML format for web browsers."""


@dataclass
class ExportMetadata:
    """Metadata for exported results."""

    timestamp: str
    """ISO 8601 timestamp of export."""

    exporter_version: str = "1.0"
    """Version of the result exporter."""

    format: str = "unknown"
    """Export format used."""

    item_count: int = 1
    """Number of items exported."""


class ResultExporter:
    """Export execution results in multiple formats."""

    VERSION = "1.0"
    """Current exporter version."""

    def export_single(
        self,
        result: Any,  # EnhancedResult
        prediction: Any,  # PerformancePrediction
        recommendations: list[Any],  # [CodeRecommendation]
        format: ExportFormat = ExportFormat.REPORT,
    ) -> str:
        """Export a single result with recommendations.

        Args:
            result: EnhancedResult from ResultProcessor.
            prediction: PerformancePrediction from PerformanceProfiler.
            recommendations: List of CodeRecommendation objects.
            format: ExportFormat specifying output format.

        Returns:
            Formatted export string in requested format.

        Raises:
            ValueError: If format is not recognized.

        Example:
            >>> exporter = ResultExporter()
            >>> output = exporter.export_single(
            ...     result, prediction, recommendations,
            ...     ExportFormat.JSON
            ... )
        """
        recommendations = recommendations or []

        match format:
            case ExportFormat.JSON:
                return self.to_json(result, prediction, recommendations)
            case ExportFormat.CSV:
                return self.to_csv(recommendations)
            case ExportFormat.TEXT:
                return self.to_text(result, prediction, recommendations)
            case ExportFormat.REPORT:
                return self.to_report(result, prediction, recommendations)
            case ExportFormat.HTML:
                return self.to_html(result, prediction, recommendations)
            case _:
                raise ValueError(f"Unsupported export format: {format}")

    def export_batch(
        self,
        results: list[Any],  # [EnhancedResult]
        predictions: list[Any],  # [PerformancePrediction]
        recommendations_list: list[list[Any]],  # [[CodeRecommendation]]
        format: ExportFormat = ExportFormat.REPORT,
    ) -> str:
        """Export multiple results with recommendations.

        Args:
            results: List of EnhancedResult objects.
            predictions: List of PerformancePrediction objects.
            recommendations_list: List of recommendation lists.
            format: ExportFormat specifying output format.

        Returns:
            Formatted export string with all results.

        Example:
            >>> batch_output = exporter.export_batch(
            ...     results, predictions, recommendations_list,
            ...     ExportFormat.CSV
            ... )
        """
        if format == ExportFormat.CSV:
            # Flatten all recommendations into single CSV
            all_recs = []
            for recs in recommendations_list:
                all_recs.extend(recs or [])
            return self.to_csv(all_recs)

        # For other formats, concatenate individual exports
        exports = []
        for result, pred, recs in zip(results, predictions, recommendations_list, strict=True):
            export = self.export_single(result, pred, recs or [], format)
            exports.append(export)

        separator = "\n" + "=" * 60 + "\n"
        return separator.join(exports)

    def to_json(
        self,
        result: Any,  # EnhancedResult
        prediction: Any,  # PerformancePrediction
        recommendations: list[Any],  # [CodeRecommendation]
    ) -> str:
        """Export to JSON format.

        Args:
            result: EnhancedResult from ResultProcessor.
            prediction: PerformancePrediction from PerformanceProfiler.
            recommendations: List of CodeRecommendation objects.

        Returns:
            JSON formatted string.
        """
        metadata = {
            "exported_at": datetime.now().isoformat(),
            "exporter_version": self.VERSION,
        }

        result_dict = {}
        if result:
            result_dict = {
                "category": getattr(result, "category", None),
                "success": getattr(result, "success", False),
                "metadata": getattr(result, "metadata", {}),
            }

        prediction_dict = {}
        if prediction:
            complexity = getattr(prediction, "complexity_level", "UNKNOWN")
            prediction_dict = {
                "predicted_time_ms": getattr(prediction, "predicted_time_ms", 0),
                "confidence": getattr(prediction, "confidence", 0),
                "complexity_level": str(complexity),
                "percentile_used": getattr(prediction, "percentile_used", 50),
            }

        recommendations_list = []
        for rec in recommendations:
            if rec:
                rec_type = getattr(rec, "recommendation_type", "UNKNOWN")
                recommendations_list.append(
                    {
                        "type": str(rec_type),
                        "description": getattr(rec, "description", ""),
                        "expected_savings_ms": getattr(rec, "expected_savings_ms", 0),
                        "confidence": getattr(rec, "confidence", 0),
                        "priority": getattr(rec, "priority", 0),
                        "estimated_effort": getattr(rec, "estimated_effort", "UNKNOWN"),
                    }
                )

        export_data = {
            "metadata": metadata,
            "result": result_dict,
            "prediction": prediction_dict,
            "recommendations": recommendations_list,
        }

        return json.dumps(export_data, indent=2)

    def to_csv(self, recommendations: list[Any]) -> str:
        """Export to CSV format.

        Args:
            recommendations: List of CodeRecommendation objects.

        Returns:
            CSV formatted string.
        """
        output = StringIO()
        fieldnames = [
            "type",
            "description",
            "expected_savings_ms",
            "confidence",
            "priority",
            "estimated_effort",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for rec in recommendations:
            if rec:
                rec_type = getattr(rec, "recommendation_type", "UNKNOWN")
                writer.writerow(
                    {
                        "type": str(rec_type),
                        "description": getattr(rec, "description", ""),
                        "expected_savings_ms": getattr(rec, "expected_savings_ms", 0),
                        "confidence": getattr(rec, "confidence", 0),
                        "priority": getattr(rec, "priority", 0),
                        "estimated_effort": getattr(rec, "estimated_effort", "UNKNOWN"),
                    }
                )

        return output.getvalue()

    def to_text(
        self,
        result: Any,  # EnhancedResult
        prediction: Any,  # PerformancePrediction
        recommendations: list[Any],  # [CodeRecommendation]
    ) -> str:
        """Export to plain text format.

        Args:
            result: EnhancedResult from ResultProcessor.
            prediction: PerformancePrediction from PerformanceProfiler.
            recommendations: List of CodeRecommendation objects.

        Returns:
            Plain text formatted string.
        """
        lines = [
            "EXECUTION RESULT EXPORT",
            "=" * 60,
            "",
        ]

        # Result section
        if result:
            category = getattr(result, "category", "unknown")
            success = getattr(result, "success", False)
            lines.extend(
                [
                    "RESULT SUMMARY",
                    "-" * 60,
                    f"Category: {category}",
                    f"Success: {success}",
                    "",
                ]
            )

        # Performance section
        if prediction:
            pred_time = getattr(prediction, "predicted_time_ms", 0)
            pred_conf = getattr(prediction, "confidence", 0)
            pred_complexity = getattr(prediction, "complexity_level", "UNKNOWN")
            lines.extend(
                [
                    "PERFORMANCE PREDICTION",
                    "-" * 60,
                    f"Estimated Time: {pred_time:.1f}ms",
                    f"Confidence: {pred_conf:.0%}",
                    f"Complexity: {pred_complexity}",
                    "",
                ]
            )

        # Recommendations section
        if recommendations:
            lines.extend(
                [
                    "RECOMMENDATIONS",
                    "-" * 60,
                    f"Total: {len(recommendations)}",
                    "",
                ]
            )
            for i, rec in enumerate(recommendations, 1):
                if rec:
                    rec_type = getattr(rec, "recommendation_type", "UNKNOWN")
                    rec_desc = getattr(rec, "description", "")
                    rec_savings = getattr(rec, "expected_savings_ms", 0)
                    rec_conf = getattr(rec, "confidence", 0)
                    rec_effort = getattr(rec, "estimated_effort", "UNKNOWN")
                    rec_priority = getattr(rec, "priority", 0)
                    lines.extend(
                        [
                            f"{i}. [{rec_type}] (Priority: {rec_priority}/5)",
                            f"   {rec_desc}",
                            f"   Savings: {rec_savings:.1f}ms | "
                            f"Confidence: {rec_conf:.0%} | Effort: {rec_effort}",
                            "",
                        ]
                    )

        return "\n".join(lines)

    def to_report(
        self,
        result: Any,  # EnhancedResult
        prediction: Any,  # PerformancePrediction
        recommendations: list[Any],  # [CodeRecommendation]
    ) -> str:
        """Export to Markdown report format.

        Args:
            result: EnhancedResult from ResultProcessor.
            prediction: PerformancePrediction from PerformanceProfiler.
            recommendations: List of CodeRecommendation objects.

        Returns:
            Markdown formatted report string.
        """
        lines = [
            "# Execution Result Report",
            "",
            "## Summary",
        ]

        # Result summary
        if result:
            success_mark = "✓" if getattr(result, "success", False) else "✗"
            category = getattr(result, "category", "unknown").upper()
            lines.extend(
                [
                    f"- **Status**: {category}",
                    f"- **Success**: {success_mark}",
                ]
            )

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines.extend(
            [
                f"- **Generated**: {timestamp}",
                "",
            ]
        )

        # Performance section
        if prediction:
            pred_time = getattr(prediction, "predicted_time_ms", 0)
            pred_conf = getattr(prediction, "confidence", 0)
            pred_complexity = getattr(prediction, "complexity_level", "UNKNOWN")
            lines.extend(
                [
                    "## Performance Analysis",
                    f"- **Predicted Time**: {pred_time:.1f}ms",
                    f"- **Confidence**: {pred_conf:.0%}",
                    f"- **Complexity**: {pred_complexity}",
                    "",
                ]
            )

        # Recommendations section
        if recommendations:
            lines.extend(
                [
                    "## Recommendations",
                    f"Found {len(recommendations)} improvement opportunity/ies.",
                    "",
                ]
            )
            for i, rec in enumerate(recommendations, 1):
                if rec:
                    priority = getattr(rec, "priority", 0)
                    rec_type = str(getattr(rec, "recommendation_type", "UNKNOWN"))
                    rec_desc = getattr(rec, "description", "")
                    rec_savings = getattr(rec, "expected_savings_ms", 0)
                    rec_conf = getattr(rec, "confidence", 0)
                    rec_effort = getattr(rec, "estimated_effort", "UNKNOWN")
                    lines.extend(
                        [
                            f"### {i}. {rec_type.upper()} (Priority {priority}/5)",
                            f"{rec_desc}",
                            "| Property | Value |",
                            "|----------|-------|",
                            f"| Expected Savings | {rec_savings:.1f}ms |",
                            f"| Confidence | {rec_conf:.0%} |",
                            f"| Effort | {rec_effort} |",
                            "",
                        ]
                    )
        else:
            lines.extend(
                [
                    "## Recommendations",
                    "No recommendations at this time.",
                    "",
                ]
            )

        return "\n".join(lines)

    def to_html(
        self,
        result: Any,  # EnhancedResult
        prediction: Any,  # PerformancePrediction
        recommendations: list[Any],  # [CodeRecommendation]
    ) -> str:
        """Export to HTML format.

        Args:
            result: EnhancedResult from ResultProcessor.
            prediction: PerformancePrediction from PerformanceProfiler.
            recommendations: List of CodeRecommendation objects.

        Returns:
            HTML formatted string.

        Note:
            This is a basic implementation. Advanced HTML generation
            can be added in Phase 5.
        """
        lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='utf-8'>",
            "<title>Execution Result Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "h1, h2 { color: #333; }",
            "table { border-collapse: collapse; width: 100%; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #f2f2f2; }",
            ".success { color: green; }",
            ".failure { color: red; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>Execution Result Report</h1>",
        ]

        # Result section
        if result:
            category = getattr(result, "category", "unknown")
            success = getattr(result, "success", False)
            status_class = "success" if success else "failure"
            lines.extend(
                [
                    "<h2>Result</h2>",
                    f"<p>Status: <span class='{status_class}'>{category.upper()}</span></p>",
                ]
            )

        # Performance section
        if prediction:
            pred_time = getattr(prediction, "predicted_time_ms", 0)
            pred_conf = getattr(prediction, "confidence", 0)
            pred_complexity = getattr(prediction, "complexity_level", "UNKNOWN")
            lines.extend(
                [
                    "<h2>Performance</h2>",
                    "<table>",
                    "<tr><th>Metric</th><th>Value</th></tr>",
                    f"<tr><td>Predicted Time</td><td>{pred_time:.1f}ms</td></tr>",
                    f"<tr><td>Confidence</td><td>{pred_conf:.0%}</td></tr>",
                    f"<tr><td>Complexity</td><td>{pred_complexity}</td></tr>",
                    "</table>",
                ]
            )

        # Recommendations section
        if recommendations:
            lines.extend(
                [
                    "<h2>Recommendations</h2>",
                    "<table>",
                    (
                        "<tr><th>Type</th><th>Description</th><th>Savings (ms)</th>"
                        "<th>Confidence</th><th>Priority</th><th>Effort</th></tr>"
                    ),
                ]
            )
            for rec in recommendations:
                if rec:
                    rec_type = getattr(rec, "recommendation_type", "UNKNOWN")
                    rec_desc = getattr(rec, "description", "")
                    rec_savings = getattr(rec, "expected_savings_ms", 0)
                    rec_conf = getattr(rec, "confidence", 0)
                    rec_priority = getattr(rec, "priority", 0)
                    rec_effort = getattr(rec, "estimated_effort", "UNKNOWN")
                    lines.append(
                        f"<tr><td>{rec_type}</td><td>{rec_desc}</td>"
                        f"<td>{rec_savings:.1f}</td><td>{rec_conf:.0%}</td>"
                        f"<td>{rec_priority}/5</td><td>{rec_effort}</td></tr>"
                    )
            lines.append("</table>")

        lines.extend(
            [
                "</body>",
                "</html>",
            ]
        )

        return "\n".join(lines)
