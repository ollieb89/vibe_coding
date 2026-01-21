"""Tests for the OutputGenerator module."""

from pathlib import Path

import pytest

from agent_discovery.generator import OutputGenerator
from agent_discovery.models import (
    Agent,
    AgentMatch,
    AgentType,
    Category,
    CodebaseProfile,
    Complexity,
)


@pytest.fixture
def sample_agent() -> Agent:
    """Create a sample agent for testing."""
    return Agent(
        name="quality-engineer",
        agent_type=AgentType.PROMPT,
        description="GitHub Copilot as a Quality Engineer for testing",
        category=Category.TESTING,
        tech_stack=["pytest", "jest", "playwright"],
        languages=["python", "typescript"],
        frameworks=["pytest", "vitest"],
        use_cases=["Testing strategy design", "Test automation"],
        complexity=Complexity.INTERMEDIATE,
        source_path="/path/to/quality-engineer.prompt.md",
        source_collection="ghc_tools/agents",
        content="# Quality Engineer\n...",
    )


@pytest.fixture
def sample_matches(sample_agent: Agent) -> list[AgentMatch]:
    """Create sample matches for testing."""
    return [
        AgentMatch(
            agent=sample_agent,
            score=0.85,
            distance=0.15,
            match_reasons=["Python testing", "Quality assurance"],
        ),
        AgentMatch(
            agent=Agent(
                name="security-engineer",
                agent_type=AgentType.PROMPT,
                description="Security-focused code review",
                category=Category.SECURITY,
                source_path="/path/to/security-engineer.prompt.md",
            ),
            score=0.72,
            distance=0.28,
            match_reasons=["Code security", "Vulnerability detection"],
        ),
        AgentMatch(
            agent=Agent(
                name="backend-architect",
                agent_type=AgentType.PROMPT,
                description="Backend architecture specialist",
                category=Category.BACKEND,
                source_path="/path/to/backend-architect.prompt.md",
                tech_stack=["fastapi", "sqlalchemy"],
                languages=["python"],
            ),
            score=0.68,
            distance=0.32,
            match_reasons=["FastAPI expertise", "Database design"],
        ),
    ]


@pytest.fixture
def sample_profile() -> CodebaseProfile:
    """Create a sample codebase profile."""
    return CodebaseProfile(
        path="/home/user/my-project",
        languages=["python", "typescript"],
        frameworks=["fastapi", "react", "pytest"],
        patterns=["async/await", "dependency injection"],
        file_count=150,
        file_types={".py": 80, ".ts": 50, ".tsx": 20},
        dependencies=["fastapi", "pydantic", "sqlalchemy"],
        dev_dependencies=["pytest", "ruff", "mypy"],
        has_tests=True,
        has_ci=True,
        has_docker=True,
    )


class TestOutputGenerator:
    """Tests for OutputGenerator class."""

    def test_init(self):
        """Test generator initialization."""
        gen = OutputGenerator()
        assert gen.vibe_tools_root is None

        gen_with_root = OutputGenerator("/path/to/vibe-tools")
        assert gen_with_root.vibe_tools_root == Path("/path/to/vibe-tools")

    def test_generate_agents_md_basic(self, sample_matches: list[AgentMatch]):
        """Test basic AGENTS.md generation."""
        gen = OutputGenerator()
        content = gen.generate_agents_md(sample_matches)

        assert "# " in content  # Has header
        assert "Recommended Agents" in content
        assert "quality-engineer" in content
        assert "security-engineer" in content
        assert "85%" in content or "85" in content  # Score shown

    def test_generate_agents_md_with_profile(
        self, sample_matches: list[AgentMatch], sample_profile: CodebaseProfile
    ):
        """Test AGENTS.md generation with codebase profile."""
        gen = OutputGenerator()
        content = gen.generate_agents_md(
            sample_matches, profile=sample_profile, project_name="My Project"
        )

        assert "My Project" in content
        assert "Project Context" in content
        assert "python" in content.lower()
        assert "fastapi" in content.lower()

    def test_generate_agents_md_without_setup(self, sample_matches: list[AgentMatch]):
        """Test AGENTS.md generation without setup section."""
        gen = OutputGenerator()
        content = gen.generate_agents_md(sample_matches, include_setup=False)

        assert "Setup" not in content or "## Setup" not in content

    def test_generate_instructions_md(
        self, sample_matches: list[AgentMatch], sample_profile: CodebaseProfile
    ):
        """Test instructions file generation."""
        gen = OutputGenerator()
        content = gen.generate_instructions_md(sample_matches, sample_profile)

        # Check frontmatter
        assert "---" in content
        assert "applyTo:" in content
        assert "description:" in content

        # Check content
        assert "Technology Stack" in content
        assert "python" in content.lower()

    def test_generate_instructions_md_no_profile(self, sample_matches: list[AgentMatch]):
        """Test instructions generation without profile."""
        gen = OutputGenerator()
        content = gen.generate_instructions_md(sample_matches, profile=None)

        assert "applyTo: '**'" in content  # Default glob

    def test_generate_chatmode_md(
        self, sample_matches: list[AgentMatch], sample_profile: CodebaseProfile
    ):
        """Test chatmode file generation."""
        gen = OutputGenerator()
        content = gen.generate_chatmode_md(
            sample_matches, sample_profile, chatmode_name="test-assistant"
        )

        # Check frontmatter
        assert "---" in content
        assert "name: test-assistant" in content
        assert "description:" in content
        assert "tags:" in content

        # Check content
        assert "Context" in content
        assert "Activation" in content
        assert "Included Agents" in content

    def test_generate_chatmode_md_custom_name(self, sample_matches: list[AgentMatch]):
        """Test chatmode with custom name."""
        gen = OutputGenerator()
        content = gen.generate_chatmode_md(
            sample_matches, profile=None, chatmode_name="my-custom-mode"
        )

        assert "name: my-custom-mode" in content
        assert "My Custom Mode" in content  # Title should be formatted

    def test_generate_full_package(
        self, sample_matches: list[AgentMatch], sample_profile: CodebaseProfile
    ):
        """Test full package generation."""
        gen = OutputGenerator()
        files = gen.generate_full_package(
            sample_matches, sample_profile, output_dir=".", project_name="Test Project"
        )

        assert "AGENTS.md" in files
        assert ".github/instructions/project.instructions.md" in files
        assert ".github/chatmodes/project-assistant.chatmode.md" in files

        # Verify content exists
        assert len(files["AGENTS.md"]) > 100
        assert "Test Project" in files["AGENTS.md"]

    def test_write_files(self, sample_matches: list[AgentMatch], tmp_path: Path):
        """Test file writing."""
        gen = OutputGenerator()
        files = {
            "AGENTS.md": "# Test AGENTS.md\nContent here.",
            ".github/instructions/test.md": "# Test instructions",
        }

        written = gen.write_files(files, str(tmp_path), overwrite=False)

        assert len(written) == 2
        assert (tmp_path / "AGENTS.md").exists()
        assert (tmp_path / ".github/instructions/test.md").exists()

        # Read back content
        content = (tmp_path / "AGENTS.md").read_text()
        assert "# Test AGENTS.md" in content

    def test_write_files_no_overwrite(self, sample_matches: list[AgentMatch], tmp_path: Path):
        """Test that existing files are not overwritten without flag."""
        gen = OutputGenerator()

        # Create existing file
        existing_file = tmp_path / "AGENTS.md"
        existing_file.write_text("Original content")

        files = {"AGENTS.md": "New content"}

        written = gen.write_files(files, str(tmp_path), overwrite=False)

        assert len(written) == 0  # No files written
        assert existing_file.read_text() == "Original content"

    def test_write_files_with_overwrite(self, tmp_path: Path):
        """Test that existing files are overwritten with flag."""
        gen = OutputGenerator()

        # Create existing file
        existing_file = tmp_path / "AGENTS.md"
        existing_file.write_text("Original content")

        files = {"AGENTS.md": "New content"}

        written = gen.write_files(files, str(tmp_path), overwrite=True)

        assert len(written) == 1
        assert existing_file.read_text() == "New content"


class TestHelperMethods:
    """Tests for helper methods."""

    def test_format_category(self):
        """Test category formatting."""
        gen = OutputGenerator()

        assert "Testing" in gen._format_category(Category.TESTING)
        assert "🧪" in gen._format_category(Category.TESTING)
        assert "Security" in gen._format_category(Category.SECURITY)
        assert "🔒" in gen._format_category(Category.SECURITY)

    def test_languages_to_glob(self):
        """Test language to glob conversion."""
        gen = OutputGenerator()

        result = gen._languages_to_glob(["python"])
        assert "*.py" in result

        result = gen._languages_to_glob(["python", "typescript"])
        assert "*.py" in result
        assert "*.ts" in result

        result = gen._languages_to_glob([])
        assert result == "**"

    def test_group_by_category(self, sample_matches: list[AgentMatch]):
        """Test grouping matches by category."""
        gen = OutputGenerator()
        groups = gen._group_by_category(sample_matches)

        assert Category.TESTING in groups
        assert Category.SECURITY in groups
        assert Category.BACKEND in groups
        assert len(groups[Category.TESTING]) == 1

    def test_format_agent_entry(self, sample_agent: Agent):
        """Test agent entry formatting."""
        gen = OutputGenerator()
        match = AgentMatch(
            agent=sample_agent,
            score=0.85,
            distance=0.15,
            match_reasons=["Testing expertise"],
        )

        lines = gen._format_agent_entry(match)
        text = "\n".join(lines)

        assert "quality-engineer" in text
        assert "85%" in text
        assert "Testing expertise" in text
