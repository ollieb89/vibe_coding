"""Tests for the agent collector."""

from pathlib import Path

from agent_discovery.collector import AgentCollector
from agent_discovery.models import AgentType, Category


class TestAgentCollector:
    """Tests for AgentCollector."""

    def test_parse_frontmatter(self, tmp_path: Path):
        """Test YAML frontmatter parsing."""
        # Create a test agent file
        agent_content = """---
name: test-agent
description: A test agent for unit testing
model: gpt-4
---

# Test Agent

This is a test agent.

## When to activate
- Testing scenarios
- Unit tests
"""
        agent_file = tmp_path / "ghc_tools" / "agents" / "test-agent.md"
        agent_file.parent.mkdir(parents=True)
        agent_file.write_text(agent_content)

        collector = AgentCollector(str(tmp_path))
        frontmatter, body = collector._parse_frontmatter(agent_content)

        assert frontmatter["name"] == "test-agent"
        assert frontmatter["description"] == "A test agent for unit testing"
        assert "# Test Agent" in body

    def test_classify_category(self, tmp_path: Path):
        """Test category classification."""
        # Create minimal structure
        (tmp_path / "ghc_tools" / "agents").mkdir(parents=True)

        collector = AgentCollector(str(tmp_path))

        # Test frontend classification
        assert (
            collector._classify_category(
                "react-expert.agent.md", "React component development and UI best practices"
            )
            == Category.FRONTEND
        )

        # Test testing classification
        assert (
            collector._classify_category(
                "playwright-tester.agent.md", "E2E testing with Playwright and test automation"
            )
            == Category.TESTING
        )

        # Test security classification
        assert (
            collector._classify_category(
                "security-engineer.agent.md", "OWASP security and vulnerability assessment"
            )
            == Category.SECURITY
        )

    def test_extract_tech_stack(self, tmp_path: Path):
        """Test tech stack extraction."""
        (tmp_path / "ghc_tools" / "agents").mkdir(parents=True)

        collector = AgentCollector(str(tmp_path))

        content = """
        This agent specializes in Next.js and React development.
        It also handles TypeScript and Tailwind CSS styling.
        """

        tech = collector._extract_tech_stack(content)

        assert "nextjs" in tech or "next.js" in tech
        assert "react" in tech
        assert "typescript" in tech
        assert "tailwind" in tech

    def test_determine_type(self, tmp_path: Path):
        """Test agent type determination."""
        (tmp_path / "ghc_tools" / "agents").mkdir(parents=True)

        collector = AgentCollector(str(tmp_path))

        assert collector._determine_type("test.agent.md", AgentType.PROMPT) == AgentType.AGENT
        assert collector._determine_type("test.prompt.md", AgentType.AGENT) == AgentType.PROMPT
        assert (
            collector._determine_type("test.instructions.md", AgentType.AGENT)
            == AgentType.INSTRUCTION
        )
        assert collector._determine_type("test.chatmode.md", AgentType.AGENT) == AgentType.CHATMODE
        assert collector._determine_type("test.md", AgentType.AGENT) == AgentType.AGENT

    def test_deduplicate(self, tmp_path: Path):
        """Test deduplication."""
        (tmp_path / "ghc_tools" / "agents").mkdir(parents=True)

        collector = AgentCollector(str(tmp_path))

        from agent_discovery.models import Agent

        agents = [
            Agent(
                name="agent1",
                agent_type=AgentType.AGENT,
                source_path="/path/1",
                content_hash="abc123",
            ),
            Agent(
                name="agent2",
                agent_type=AgentType.AGENT,
                source_path="/path/2",
                content_hash="def456",
            ),
            Agent(
                name="agent1-dup",
                agent_type=AgentType.AGENT,
                source_path="/path/3",
                content_hash="abc123",  # Same hash as agent1
            ),
        ]

        unique = collector.deduplicate(agents)

        assert len(unique) == 2
        assert unique[0].name == "agent1"
        assert unique[1].name == "agent2"
