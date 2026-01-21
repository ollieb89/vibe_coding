"""Agent synthesizer - Creates comprehensive agents from specialist content."""

import re
from pathlib import Path
from typing import Any

from agent_discovery.models import AgentMatch


class ContentExtractor:
    """Extract structured content from agent markdown files."""

    @staticmethod
    def extract_from_match(match: AgentMatch, base_path: str = "./") -> dict[str, Any]:
        """Extract structured content from an agent match.

        Args:
            match: AgentMatch with source_path
            base_path: Base directory to find agent files

        Returns:
            Dictionary with extracted sections
        """
        content = {
            "name": match.agent.name,
            "description": match.agent.description,
            "persona": "",
            "triggers": [],
            "behavioral_mindset": "",
            "core_responsibilities": [],
            "key_actions": [],
            "when_to_activate": [],
            "focus_areas": {},
            "principles": {},
            "keywords": match.agent.subjects or [],
        }

        # Try to read the full agent file
        source_file = Path(base_path) / match.agent.source_path
        if source_file.exists():
            try:
                text = source_file.read_text(encoding="utf-8")
                content.update(ContentExtractor._parse_agent_file(text))
            except Exception:
                pass  # Fall back to metadata only

        return content

    @staticmethod
    def _parse_agent_file(text: str) -> dict[str, Any]:
        """Parse structured sections from agent markdown.

        Args:
            text: Full agent markdown content

        Returns:
            Dictionary with extracted sections
        """
        result = {
            "persona": "",
            "triggers": [],
            "behavioral_mindset": "",
            "core_responsibilities": [],
            "key_actions": [],
            "when_to_activate": [],
            "focus_areas": {},
            "principles": {},
        }

        # Extract role/persona section
        role_match = re.search(r"##\s+Role\s*\n(.*?)(?=##|\Z)", text, re.DOTALL | re.IGNORECASE)
        if role_match:
            result["persona"] = role_match.group(1).strip()

        # Extract triggers
        trigger_match = re.search(
            r"##\s+Triggers?\s*\n(.*?)(?=##|\Z)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if trigger_match:
            trigger_text = trigger_match.group(1)
            triggers = re.findall(r"[-•]\s*(.+)", trigger_text)
            result["triggers"] = [t.strip() for t in triggers]

        # Extract behavioral mindset
        mindset_match = re.search(
            r"##\s+Behavioral?\s+Mindset\s*\n(.*?)(?=##|\Z)", text, re.DOTALL | re.IGNORECASE
        )
        if mindset_match:
            result["behavioral_mindset"] = mindset_match.group(1).strip()

        # Extract core responsibilities/behaviors
        resp_match = re.search(
            r"##\s+(?:Core\s+)?(?:Responsibilities|Behaviors)\s*\n(.*?)(?=##|\Z)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if resp_match:
            resp_text = resp_match.group(1)
            # Extract subsections like "### 1. Name"
            subsections = re.findall(r"###\s+\d+\.\s+([^-•]+?)(?=###|\Z)", resp_text, re.DOTALL)
            result["core_responsibilities"] = [s.strip() for s in subsections if s.strip()]

        # Extract key actions
        actions_match = re.search(
            r"##\s+(?:Key\s+)?Actions\s*\n(.*?)(?=##|\Z)", text, re.DOTALL | re.IGNORECASE
        )
        if actions_match:
            actions_text = actions_match.group(1)
            # Extract numbered items like "1. **Name**"
            actions = re.findall(r"\d+\.\s+\*?\*?([^*]+)\*?\*?", actions_text)
            result["key_actions"] = [a.strip() for a in actions if a.strip()]

        # Extract "When to Activate" section
        activate_match = re.search(
            r"##\s+When\s+to\s+Activate\s*\n(.*?)(?=##|\Z)", text, re.DOTALL | re.IGNORECASE
        )
        if activate_match:
            activate_text = activate_match.group(1)
            activations = re.findall(r"[-•]\s*(.+)", activate_text)
            result["when_to_activate"] = [a.strip() for a in activations]

        # Extract focus areas (sections with subsections)
        focus_match = re.search(
            r"##\s+Focus\s+Areas\s*\n(.*?)(?=##|\Z)", text, re.DOTALL | re.IGNORECASE
        )
        if focus_match:
            focus_text = focus_match.group(1)
            # Extract "### Area Name" and bullet points
            areas = re.findall(r"###\s+([^-•\n]+)\n((?:[-•]\s+.+\n?)*)", focus_text)
            for area_name, area_content in areas:
                bullets = re.findall(r"[-•]\s*(.+)", area_content)
                result["focus_areas"][area_name.strip()] = [b.strip() for b in bullets]

        # Extract principles
        principle_match = re.search(
            r"##\s+(?:Key\s+)?Principles\s*\n(.*?)(?=##|\Z)", text, re.DOTALL | re.IGNORECASE
        )
        if principle_match:
            principle_text = principle_match.group(1)
            # Extract "### Principle Name" and content
            principles = re.findall(r"###\s+([^\n]+)\n(.*?)(?=###|\Z)", principle_text, re.DOTALL)
            for principle_name, principle_content in principles:
                result["principles"][principle_name.strip()] = principle_content.strip()

        return result


class AgentSynthesizer:
    """Synthesize a comprehensive agent from multiple specialist agents."""

    def __init__(self, base_path: str = "./"):
        """Initialize synthesizer.

        Args:
            base_path: Base directory for agent files
        """
        self.base_path = base_path
        self.extractor = ContentExtractor()

    def synthesize(
        self,
        subject: str,
        matches: list[AgentMatch],
        top_n: int = 5,
    ) -> str:
        """Synthesize a comprehensive agent from top matches.

        Args:
            subject: The subject/domain for the agent
            matches: List of AgentMatch objects
            top_n: Number of top matches to use

        Returns:
            Generated agent markdown content
        """
        # Extract content from top matches
        extracted = []
        for match in matches[:top_n]:
            content = self.extractor.extract_from_match(match, self.base_path)
            content["score"] = match.score
            extracted.append(content)

        if not extracted:
            return self._generate_empty_agent(subject)

        # Synthesize unified content
        persona = self._synthesize_persona(subject, extracted)
        triggers = self._deduplicate_triggers(extracted)
        behaviors = self._synthesize_behaviors(extracted)
        focus_areas = self._merge_focus_areas(extracted)
        principles = self._merge_principles(extracted)

        # Build markdown
        return self._build_agent_markdown(
            subject=subject,
            persona=persona,
            triggers=triggers,
            behaviors=behaviors,
            focus_areas=focus_areas,
            principles=principles,
            specialists=extracted,
        )

    def _synthesize_persona(self, subject: str, extracted: list[dict]) -> str:
        """Create a unified persona statement.

        Args:
            subject: Subject/domain
            extracted: List of extracted content

        Returns:
            Persona statement
        """
        if not extracted:
            return f"You are GitHub Copilot as a {subject.title()} Expert."

        # Use first agent's persona if strong enough
        if extracted[0].get("persona"):
            base = extracted[0]["persona"]
            if len(base) > 50:  # Substantial persona
                return base

        # Synthesize from specialist descriptions
        descriptions = [e.get("description", "").strip() for e in extracted if e.get("description")]
        descriptions = [d for d in descriptions if d and len(d) > 10]

        if descriptions:
            # Take the most complete description as basis
            best_desc = max(descriptions, key=len)
            return (
                f"You are GitHub Copilot as a {subject.title()} Expert, specialized in {best_desc}."
            )

        return f"You are GitHub Copilot as a {subject.title()} Expert with comprehensive knowledge across the field."

    def _deduplicate_triggers(self, extracted: list[dict]) -> list[str]:
        """Combine and deduplicate triggers/activation conditions.

        Args:
            extracted: List of extracted content

        Returns:
            Deduplicated list of triggers
        """
        triggers_set: set[str] = set()
        triggers_list: list[str] = []

        for item in extracted:
            for trigger in item.get("triggers", []):
                trigger_normalized = trigger.lower().strip()
                if trigger_normalized not in triggers_set:
                    triggers_set.add(trigger_normalized)
                    triggers_list.append(trigger)

        # Also add "when to activate" items
        for item in extracted:
            for activation in item.get("when_to_activate", []):
                activation_normalized = activation.lower().strip()
                if activation_normalized not in triggers_set:
                    triggers_set.add(activation_normalized)
                    triggers_list.append(activation)

        # Limit to top triggers
        return triggers_list[:10]

    def _synthesize_behaviors(self, extracted: list[dict]) -> list[tuple[str, str]]:
        """Create unified core behaviors from specialists.

        Args:
            extracted: List of extracted content

        Returns:
            List of (behavior_name, description) tuples
        """
        behaviors_dict: dict[str, str] = {}

        # Collect key actions as behaviors
        for item in extracted:
            for action in item.get("key_actions", []):
                # Format "Action: description" if it follows that pattern
                if ":" in action:
                    name, desc = action.split(":", 1)
                    name = name.strip()
                    desc = desc.strip()
                else:
                    name = action
                    desc = ""

                # Avoid duplicates
                name_lower = name.lower()
                if name_lower not in behaviors_dict:
                    behaviors_dict[name_lower] = f"{name}: {desc}" if desc else name

        # Also collect from core responsibilities
        for item in extracted:
            for resp in item.get("core_responsibilities", []):
                if resp and resp.lower() not in behaviors_dict:
                    behaviors_dict[resp.lower()] = resp

        # Convert to list of tuples and limit
        behaviors = [
            (name.replace("_", " ").title(), desc) for name, desc in behaviors_dict.items()
        ]
        return behaviors[:7]  # Limit to top 7 behaviors

    def _merge_focus_areas(self, extracted: list[dict]) -> dict[str, list[str]]:
        """Merge focus areas from multiple specialists.

        Args:
            extracted: List of extracted content

        Returns:
            Dictionary of focus_area -> capabilities
        """
        merged: dict[str, set[str]] = {}

        for item in extracted:
            for area_name, capabilities in item.get("focus_areas", {}).items():
                if area_name not in merged:
                    merged[area_name] = set()
                merged[area_name].update(capabilities)

        # Convert sets to sorted lists, limit per area
        result = {}
        for area_name, caps in merged.items():
            result[area_name] = sorted(caps)[:5]

        # Limit to top 5 focus areas
        return dict(sorted(result.items())[:5])

    def _merge_principles(self, extracted: list[dict]) -> dict[str, str]:
        """Merge key principles from specialists.

        Args:
            extracted: List of extracted content

        Returns:
            Dictionary of principle_name -> description
        """
        merged: dict[str, str] = {}

        for item in extracted:
            for principle_name, description in item.get("principles", {}).items():
                if principle_name not in merged:
                    merged[principle_name] = description

        # Limit to top 5 principles
        return dict(sorted(merged.items())[:5])

    def _build_agent_markdown(
        self,
        subject: str,
        persona: str,
        triggers: list[str],
        behaviors: list[tuple[str, str]],
        focus_areas: dict[str, list[str]],
        principles: dict[str, str],
        specialists: list[dict],
    ) -> str:
        """Build final agent markdown.

        Args:
            subject: Subject/domain
            persona: Persona statement
            triggers: List of activation triggers
            behaviors: List of (name, description) tuples
            focus_areas: Dictionary of area -> capabilities
            principles: Dictionary of principle -> description
            specialists: List of specialist agents used

        Returns:
            Complete agent markdown
        """
        agent_name = f"ultimate-{subject.lower().replace(' ', '-')}"
        lines = [
            "---",
            f"name: {agent_name}",
            f"description: Ultimate {subject} specialist combining {len(specialists)} expert perspectives",
            f"tags: [{subject}, ultimate, composite]",
            "---",
            "",
            f"# Copilot {subject.title()} Expert",
            "",
            f"{persona}",
            "",
            "## When to Activate",
            "",
        ]

        # Add triggers
        for trigger in triggers:
            lines.append(f"- {trigger}")

        if not triggers:
            lines.append(f"- Any {subject}-related task or challenge")

        lines.extend(
            [
                "",
                "## Core Behaviors",
                "",
            ]
        )

        # Add behaviors
        for behavior_name, behavior_desc in behaviors:
            if behavior_desc:
                lines.append(f"- **{behavior_name}**: {behavior_desc}")
            else:
                lines.append(f"- **{behavior_name}**")

        # Add focus areas if present
        if focus_areas:
            lines.extend(
                [
                    "",
                    "## Focus Areas",
                    "",
                ]
            )
            for area_name, capabilities in focus_areas.items():
                lines.append(f"### {area_name}")
                lines.append("")
                for cap in capabilities:
                    lines.append(f"- {cap}")
                lines.append("")

        # Add principles if present
        if principles:
            lines.extend(
                [
                    "## Key Principles",
                    "",
                ]
            )
            for principle_name, description in principles.items():
                lines.append(f"### {principle_name}")
                lines.append("")
                lines.append(description)
                lines.append("")

        # Add included specialists
        lines.extend(
            [
                "## Included Specialists",
                "",
                "This ultimate agent synthesizes expertise from:",
                "",
            ]
        )

        for specialist in specialists:
            score = specialist.get("score", 0)
            score_pct = int(score * 100) if isinstance(score, float) else "-"
            lines.append(
                f"- **{specialist['name']}** ({score_pct}% match) - {specialist['description']}"
            )

        lines.extend(
            [
                "",
                "## Usage Recommendations",
                "",
                "This agent is optimized for:",
                f"- Complex {subject}-related challenges requiring multiple perspectives",
                "- Situations demanding comprehensive expertise across the domain",
                "- Projects where quality and best practices are priorities",
                "",
                f"For specialized sub-domains within {subject}, consider using individual specialist agents.",
            ]
        )

        return "\n".join(lines)

    def _generate_empty_agent(self, subject: str) -> str:
        """Generate a minimal agent when no specialists found.

        Args:
            subject: Subject/domain

        Returns:
            Minimal agent markdown
        """
        agent_name = f"ultimate-{subject.lower().replace(' ', '-')}"
        return f"""---
name: {agent_name}
description: Ultimate {subject} specialist
tags: [{subject}, ultimate]
---

# Copilot {subject.title()} Expert

You are an expert in {subject}, ready to provide comprehensive guidance and assistance.

## When to Activate

- Any {subject}-related task

## Core Behaviors

- **Expert Guidance**: Provide authoritative advice based on best practices
- **Comprehensive Approach**: Consider multiple perspectives and approaches
- **Practical Solutions**: Deliver implementable, real-world solutions

## Focus Areas

- Core {subject} practices and patterns
- Best practices and standards
- Industry-standard approaches

## Key Principles

### Quality First
Always prioritize quality, correctness, and best practices.

### Comprehensive Thinking
Consider all relevant aspects and potential implications.
"""
