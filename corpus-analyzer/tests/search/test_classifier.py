"""Tests for ConstructClassifier rule-based and LLM fallback classification."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from corpus_analyzer.search.classifier import classify_by_rules, classify_file, ClassificationResult


def test_classify_skill_by_path() -> None:
    result = classify_by_rules(Path("skills/my-skill.md"), "body")
    assert result is not None
    assert result.construct_type == "skill"
    assert result.confidence == 0.6
    assert result.source == "rule_based"


def test_classify_prompt_by_path() -> None:
    result = classify_by_rules(Path("prompts/rewrite.md"), "body")
    assert result is not None
    assert result.construct_type == "prompt"
    assert result.confidence == 0.6
    assert result.source == "rule_based"


def test_classify_workflow_by_path() -> None:
    result = classify_by_rules(Path("workflows/deploy.md"), "body")
    assert result is not None
    assert result.construct_type == "workflow"
    assert result.confidence == 0.6
    assert result.source == "rule_based"


def test_classify_code_by_extension() -> None:
    result = classify_by_rules(Path("some/dir/tool.py"), "body")
    assert result is not None
    assert result.construct_type == "code"
    assert result.confidence == 0.6
    assert result.source == "rule_based"
    result = classify_by_rules(Path("some/dir/tool.ts"), "body")
    assert result.construct_type == "code"
    result = classify_by_rules(Path("some/dir/tool.js"), "body")
    assert result.construct_type == "code"


def test_classify_agent_config_by_frontmatter() -> None:
    text = """---
name: My Agent
description: Agent behavior config
tools:
  - bash
---
content
"""
    result = classify_by_rules(Path("configs/agent.md"), text)
    assert result is not None
    assert result.construct_type == "agent_config"
    assert result.confidence == 0.6
    assert result.source == "rule_based"


def test_classify_skill_by_frontmatter() -> None:
    text = """---
name: My Skill
description: Skill docs
---
content
"""
    result = classify_by_rules(Path("docs/anything.md"), text)
    assert result is not None
    assert result.construct_type == "skill"
    assert result.confidence == 0.6
    assert result.source == "rule_based"


def test_llm_fallback_called_when_rules_unclear() -> None:
    with patch("corpus_analyzer.search.classifier.ollama.generate") as mock_generate:
        mock_generate.return_value.response = "prompt"
        result = classify_file(
            Path("misc/notes.txt"),
            "This file has no obvious rule signals.",
            model="mistral",
        )

    assert result.construct_type == "prompt"
    assert result.confidence == 0.8
    assert result.source == "llm"
    mock_generate.assert_called_once()


def test_fallback_to_documentation_when_llm_disabled() -> None:
    result = classify_file(
        Path("misc/notes.txt"),
        "Ambiguous content.",
        model="mistral",
        use_llm=False,
    )
    assert result.construct_type == "documentation"
    assert result.confidence == 0.5
    assert result.source == "rule_based"

    with patch(
        "corpus_analyzer.search.classifier.ollama.generate",
        side_effect=RuntimeError("boom"),
    ):
        result_on_error = classify_file(
            Path("misc/notes.txt"),
            "Ambiguous content.",
            model="mistral",
            use_llm=True,
        )

    assert result_on_error.construct_type == "documentation"
    assert result_on_error.confidence == 0.5
    assert result_on_error.source == "rule_based"


def test_classify_frontmatter_type_skill() -> None:
    text = "---\ntype: skill\n---\n"
    result = classify_file(Path("doc.md"), text, model="mistral", use_llm=False)
    assert result.construct_type == "skill"
    assert result.confidence == 0.95
    assert result.source == "frontmatter"


def test_classify_frontmatter_type_case_insensitive() -> None:
    text = "---\nType: Skill\n---\n"
    result = classify_file(Path("doc.md"), text, model="mistral", use_llm=False)
    assert result.construct_type == "skill"


def test_classify_frontmatter_component_type() -> None:
    text = "---\ncomponent_type: prompt\n---\n"
    result = classify_file(Path("doc.md"), text, model="mistral", use_llm=False)
    assert result.construct_type == "prompt"
    assert result.confidence == 0.95
    assert result.source == "frontmatter"


def test_classify_frontmatter_camelcase_alias() -> None:
    text = "---\ncomponentType: workflow\n---\n"
    result = classify_file(Path("doc.md"), text, model="mistral", use_llm=False)
    assert result.construct_type == "workflow"
    assert result.confidence == 0.95
    assert result.source == "frontmatter"


def test_classify_frontmatter_type_beats_component_type() -> None:
    text = "---\ntype: skill\ncomponent_type: prompt\n---\n"
    result = classify_file(Path("doc.md"), text, model="mistral", use_llm=False)
    assert result.construct_type == "skill"
    assert result.confidence == 0.95
    assert result.source == "frontmatter"


def test_classify_frontmatter_unknown_value_fallthrough() -> None:
    text = "---\ntype: skills\n---\n"
    result = classify_file(Path("doc.md"), text, model="mistral", use_llm=False)
    assert result.construct_type == "documentation"
    assert result.source == "rule_based"


def test_classify_frontmatter_nonstring_value_fallthrough() -> None:
    text = "---\ntype: 42\n---\n"
    result = classify_file(Path("doc.md"), text, model="mistral", use_llm=False)
    assert result.construct_type == "documentation"


def test_classify_frontmatter_malformed_yaml_fallthrough() -> None:
    text = "---\ntype: [unclosed\n---\n"
    result = classify_file(Path("doc.md"), text, model="mistral", use_llm=False)
    assert result.construct_type == "documentation"


def test_classify_frontmatter_tags_substring_match() -> None:
    text = "---\ntags: [skill-template]\n---\n"
    result = classify_file(Path("doc.md"), text, model="mistral", use_llm=False)
    assert result.construct_type == "skill"
    assert result.confidence == 0.70
    assert result.source == "frontmatter"


def test_classify_frontmatter_tags_case_insensitive() -> None:
    text = "---\ntags: [PROMPT-HELPER]\n---\n"
    result = classify_file(Path("doc.md"), text, model="mistral", use_llm=False)
    assert result.construct_type == "prompt"
    assert result.confidence == 0.70


def test_classify_frontmatter_tags_ignored_when_type_resolves() -> None:
    text = "---\ntype: workflow\ntags: [skill]\n---\n"
    result = classify_file(Path("doc.md"), text, model="mistral", use_llm=False)
    assert result.construct_type == "workflow"
    assert result.confidence == 0.95


def test_classify_frontmatter_unmatched_tags_fallthrough() -> None:
    text = "---\ntags: [unrelated]\n---\n"
    result = classify_file(Path("doc.md"), text, model="mistral", use_llm=False)
    assert result.construct_type == "documentation"
    assert result.source == "rule_based"
