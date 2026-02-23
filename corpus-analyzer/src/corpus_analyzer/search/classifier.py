"""Construct type classification for indexed files.

Classification is two-tier:
1) frontmatter explicit types (highest confidence)
2) rule-based heuristics (fast, deterministic)
3) LLM fallback for ambiguous files (optional)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import frontmatter  # type: ignore[import-untyped]
import ollama

CONSTRUCT_TYPES: frozenset[str] = frozenset(
    {"skill", "prompt", "workflow", "agent_config", "code", "documentation"}
)


@dataclass
class ClassificationResult:
    """Result of construct type classification.

    Attributes:
        construct_type: One of the recognized construct types
        confidence: Confidence score (0.0-1.0)
        source: Origin of classification ("frontmatter", "rule_based", or "llm")
    """

    construct_type: str
    confidence: float
    source: str

LLM_CLASSIFY_PROMPT = """You are classifying a file in an AI agent library.
Choose exactly one label from: skill, prompt, workflow, agent_config, code, documentation.

- skill: A reusable capability or tool definition
- prompt: A prompt template or instruction set
- workflow: A multi-step process or pipeline definition
- agent_config: An agent configuration with name, description, and tools
- code: Source code (implementation file)
- documentation: Everything else (readme, guide, reference)

File: {filename}
Content (first 500 chars): {content}

Respond with only the label (one word):"""


def classify_by_frontmatter(file_path: Path, text: str) -> ClassificationResult | None:
    """Classify a file using explicit frontmatter type declarations.

    Checks for `type:` and `component_type:` (or `componentType:`) keys
    with confidence 0.95 if the value matches a known construct type.
    Falls back to tags substring matching with confidence 0.70.

    Returns None when no frontmatter classification is possible.
    """
    suffix = file_path.suffix.lower()
    if suffix not in {".md", ".yaml", ".yml"}:
        return None

    try:
        post = frontmatter.loads(text)
        metadata = post.metadata
        if not metadata or not isinstance(metadata, dict):
            return None

        # Normalize keys: lowercase, map camelCase aliases
        norm_meta: dict[str, object] = {}
        for k, v in metadata.items():
            if isinstance(k, str):
                key_lower = k.lower()
                norm_meta[key_lower] = v

        # Handle componentType camelCase alias
        if "componenttype" in norm_meta and "component_type" not in norm_meta:
            norm_meta["component_type"] = norm_meta["componenttype"]

        # 1. Check type: key first (highest priority)
        if "type" in norm_meta:
            val = str(norm_meta["type"]).lower()
            if val in CONSTRUCT_TYPES:
                return ClassificationResult(val, 0.95, "frontmatter")

        # 2. Check component_type: key
        if "component_type" in norm_meta:
            val = str(norm_meta["component_type"]).lower()
            if val in CONSTRUCT_TYPES:
                return ClassificationResult(val, 0.95, "frontmatter")

        # 3. Check tags: substring match (only if no explicit type: found)
        if "tags" in norm_meta and isinstance(norm_meta["tags"], list):
            for tag in norm_meta["tags"]:
                if not isinstance(tag, str):
                    continue
                tag_lower = tag.lower()
                for construct in CONSTRUCT_TYPES:
                    if construct in tag_lower:
                        return ClassificationResult(construct, 0.70, "frontmatter")

    except Exception:
        # Malformed YAML or parse errors: treat as absent
        pass

    return None


def classify_by_rules(file_path: Path, text: str) -> ClassificationResult | None:
    """Classify a file using deterministic rule signals.

    Returns None when no rule matches, allowing LLM fallback.
    """

    suffix = file_path.suffix.lower()

    # 1) Extension-based code signal
    if suffix in {".py", ".ts", ".js"}:
        return ClassificationResult("code", 0.6, "rule_based")

    # 2-4) Path-part signals
    parts = [part.lower() for part in file_path.parts]
    if any(part == "skills" or "skill" in part for part in parts):
        return ClassificationResult("skill", 0.6, "rule_based")
    if any(part == "prompts" or "prompt" in part for part in parts):
        return ClassificationResult("prompt", 0.6, "rule_based")
    if any(part == "workflows" or "workflow" in part for part in parts):
        return ClassificationResult("workflow", 0.6, "rule_based")

    # 5-6) Frontmatter signals (structural: name + description)
    if suffix in {".md", ".yaml", ".yml"}:
        try:
            post = frontmatter.loads(text)
            metadata = post.metadata
            has_name = "name" in metadata
            has_description = "description" in metadata
            has_tools = "tools" in metadata

            if has_name and has_description and has_tools:
                return ClassificationResult("agent_config", 0.6, "rule_based")
            if has_name and has_description:
                return ClassificationResult("skill", 0.6, "rule_based")
        except Exception:
            # Invalid or missing frontmatter is not fatal for classification.
            pass

    # 7-8) Filename stem signals
    stem = file_path.stem.lower()
    if "workflow" in stem:
        return ClassificationResult("workflow", 0.6, "rule_based")
    if "prompt" in stem:
        return ClassificationResult("prompt", 0.6, "rule_based")

    return None


def classify_file(
    file_path: Path, text: str, model: str, *, use_llm: bool = True
) -> ClassificationResult:
    """Classify a file into one of the six construct types.

    Priority order:
    1. Frontmatter explicit type declarations (highest confidence)
    2. Rule-based heuristic signals
    3. LLM fallback for ambiguous files (if enabled)
    4. Default to documentation
    """
    # 1. Frontmatter explicit types (highest priority, confidence 0.95)
    fm_result = classify_by_frontmatter(file_path, text)
    if fm_result is not None:
        return fm_result

    # 2. Rule-based signals
    rule_result = classify_by_rules(file_path, text)
    if rule_result is not None:
        return rule_result

    if not use_llm:
        return ClassificationResult("documentation", 0.5, "rule_based")

    prompt = LLM_CLASSIFY_PROMPT.format(
        filename=file_path.as_posix(),
        content=text[:500],
    )

    try:
        response = ollama.generate(model=model, prompt=prompt)
        response_text = str(getattr(response, "response", "")).lower()

        for token in re.findall(r"[a-z_]+", response_text):
            if token in CONSTRUCT_TYPES:
                return ClassificationResult(str(token), 0.8, "llm")
    except Exception:
        return ClassificationResult("documentation", 0.5, "rule_based")

    return ClassificationResult("documentation", 0.5, "rule_based")
