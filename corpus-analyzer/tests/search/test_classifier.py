"""Tests for ConstructClassifier rule-based and LLM fallback classification."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from corpus_analyzer.search.classifier import (
    CONSTRUCT_TYPES,
    classify_by_rules,
    classify_file,
)


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


def test_classify_agent_by_frontmatter_name_description_tools() -> None:
    """Structural frontmatter with name+description+tools → agent (renamed from agent_config)."""
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
    assert result.construct_type == "agent"
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


# --- New construct types: rule, command, agent ---


def test_construct_types_includes_rule_and_command() -> None:
    """CONSTRUCT_TYPES frozenset must contain the two new types."""
    assert "rule" in CONSTRUCT_TYPES
    assert "command" in CONSTRUCT_TYPES


def test_construct_types_uses_agent_not_agent_config() -> None:
    """agent replaces agent_config as the canonical stored value."""
    assert "agent" in CONSTRUCT_TYPES
    assert "agent_config" not in CONSTRUCT_TYPES


def test_classify_rule_by_cursorrules_filename() -> None:
    """.cursorrules file (dotfile) is classified as rule."""
    result = classify_by_rules(Path(".cursorrules"), "project rules")
    assert result is not None
    assert result.construct_type == "rule"


def test_classify_rule_by_cursorrules_extension() -> None:
    """File with .cursorrules extension is classified as rule."""
    result = classify_by_rules(Path("project.cursorrules"), "project rules")
    assert result is not None
    assert result.construct_type == "rule"


def test_classify_rule_by_clinerules_filename() -> None:
    """.clinerules file is classified as rule."""
    result = classify_by_rules(Path(".clinerules"), "cline rules")
    assert result is not None
    assert result.construct_type == "rule"


def test_classify_rule_by_claude_md_filename() -> None:
    """A file named CLAUDE.md is classified as rule."""
    result = classify_by_rules(Path("CLAUDE.md"), "project guidance")
    assert result is not None
    assert result.construct_type == "rule"


def test_classify_rule_by_rules_directory() -> None:
    """File inside a 'rules' directory is classified as rule."""
    result = classify_by_rules(Path("rules/no-agents.md"), "rule content")
    assert result is not None
    assert result.construct_type == "rule"


def test_classify_command_by_commands_directory() -> None:
    """File inside a 'commands' directory is classified as command."""
    result = classify_by_rules(Path("commands/deploy.md"), "command content")
    assert result is not None
    assert result.construct_type == "command"


def test_classify_command_by_cmd_stem() -> None:
    """File whose stem contains 'cmd' is classified as command."""
    result = classify_by_rules(Path("my-project.cmd.md"), "command content")
    assert result is not None
    assert result.construct_type == "command"


def test_classify_agent_by_agents_directory() -> None:
    """File inside an 'agents' directory is classified as agent."""
    result = classify_by_rules(Path("agents/my-agent.md"), "agent definition")
    assert result is not None
    assert result.construct_type == "agent"


def test_frontmatter_type_agent_is_recognised() -> None:
    """Explicit type: agent in frontmatter returns agent at 0.95 confidence."""
    text = "---\ntype: agent\n---\n"
    result = classify_file(Path("doc.md"), text, model="mistral", use_llm=False)
    assert result.construct_type == "agent"
    assert result.confidence == 0.95
    assert result.source == "frontmatter"


def test_frontmatter_type_rule_is_recognised() -> None:
    """Explicit type: rule in frontmatter returns rule at 0.95 confidence."""
    text = "---\ntype: rule\n---\n"
    result = classify_file(Path("doc.md"), text, model="mistral", use_llm=False)
    assert result.construct_type == "rule"
    assert result.confidence == 0.95
    assert result.source == "frontmatter"


def test_frontmatter_type_command_is_recognised() -> None:
    """Explicit type: command in frontmatter returns command at 0.95 confidence."""
    text = "---\ntype: command\n---\n"
    result = classify_file(Path("doc.md"), text, model="mistral", use_llm=False)
    assert result.construct_type == "command"
    assert result.confidence == 0.95
    assert result.source == "frontmatter"
