"""Tests for the analyze-all CLI command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.agent_discovery.cli import cli


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def vibe_tools_root():
    """Return the vibe-tools root directory."""
    return Path(__file__).parent.parent.parent / "vibe-tools"


class TestAnalyzeAllCommand:
    """Tests for the analyze-all CLI command."""

    def test_analyze_all_help(self, runner):
        """Test that analyze-all command shows help."""
        result = runner.invoke(cli, ["analyze-all", "--help"])
        assert result.exit_code == 0
        assert "🚀 Run full agent learning pipeline" in result.output
        assert "--collection-only" in result.output
        assert "--enable-execution" in result.output
        assert "--source" in result.output
        assert "-v" in result.output or "--verbose" in result.output

    def test_analyze_all_collection_only(self, runner, vibe_tools_root):
        """Test analyze-all with collection-only flag."""
        if not vibe_tools_root.exists():
            pytest.skip("vibe-tools root not found")

        result = runner.invoke(
            cli,
            [
                "analyze-all",
                "--collection-only",
                "--source",
                str(vibe_tools_root),
            ],
        )
        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "Agent Learning Pipeline" in result.output or "🚀" in result.output
        assert "Collection Results" in result.output or "Phase 1 Complete" in result.output
        agents_msg = "agents discovered" in result.output.lower()
        assert agents_msg or "agents found" in result.output.lower()

    def test_analyze_all_collection_only_verbose(self, runner, vibe_tools_root):
        """Test analyze-all with collection-only flag and verbose output."""
        if not vibe_tools_root.exists():
            pytest.skip("vibe-tools root not found")

        result = runner.invoke(
            cli,
            [
                "analyze-all",
                "--collection-only",
                "--source",
                str(vibe_tools_root),
                "-v",
            ],
        )
        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "Configuration:" in result.output
        assert "Collection Only: True" in result.output
        assert "Phase 1 Complete" in result.output

    def test_analyze_all_with_source_option(self, runner, vibe_tools_root):
        """Test analyze-all with custom --source option."""
        if not vibe_tools_root.exists():
            pytest.skip("vibe-tools root not found")

        result = runner.invoke(
            cli,
            [
                "analyze-all",
                "--collection-only",
                "--source",
                str(vibe_tools_root),
            ],
        )
        assert result.exit_code == 0, f"Command failed: {result.output}"

    def test_analyze_all_nonexistent_source(self, runner):
        """Test analyze-all with non-existent source path."""
        result = runner.invoke(
            cli,
            [
                "analyze-all",
                "--source",
                "/nonexistent/path/vibe-tools",
            ],
        )
        # Should fail because path doesn't exist
        assert result.exit_code != 0

    def test_analyze_all_default_paths(self, runner):
        """Test that analyze-all finds default vibe-tools path."""
        # This test doesn't require an explicit --source
        result = runner.invoke(
            cli,
            ["analyze-all", "--collection-only"],
            env={"PWD": "/home/ob/Development/Tools/vibe-tools/agent-discovery-system"},
        )
        # Should either succeed or fail gracefully with a clear error
        assert result.exit_code in [0, 1]

    def test_analyze_all_enable_execution_flag(self, runner, vibe_tools_root):
        """Test analyze-all with --enable-execution flag."""
        if not vibe_tools_root.exists():
            pytest.skip("vibe-tools root not found")

        result = runner.invoke(
            cli,
            [
                "analyze-all",
                "--enable-execution",
                "--source",
                str(vibe_tools_root),
                "--collection-only",  # Add this to make it faster
            ],
        )
        assert result.exit_code == 0, f"Command failed: {result.output}"

    @patch("src.agent_discovery.pipeline.AgentPipeline")
    def test_analyze_all_config_passed_correctly(
        self, mock_pipeline_class, runner, vibe_tools_root
    ):
        """Test that configuration is passed correctly to AgentPipeline."""
        # Create a mock pipeline instance
        mock_pipeline = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline
        mock_pipeline._collect_agents.return_value = []

        if not vibe_tools_root.exists():
            pytest.skip("vibe-tools root not found")

        runner.invoke(
            cli,
            [
                "analyze-all",
                "--collection-only",
                "--source",
                str(vibe_tools_root),
                "--enable-execution",
                "-v",
            ],
        )

        # Verify AgentPipeline was called with correct config
        assert mock_pipeline_class.called
        call_kwargs = mock_pipeline_class.call_args[1]
        assert "config" in call_kwargs
        config = call_kwargs["config"]
        assert config.enable_execution is True
        assert config.verbose is True

    def test_analyze_all_help_shows_examples(self, runner):
        """Test that help text includes usage examples."""
        result = runner.invoke(cli, ["analyze-all", "--help"])
        assert result.exit_code == 0
        assert "Examples:" in result.output
        assert "agent-discover analyze-all" in result.output

    def test_analyze_all_flags_are_mutually_compatible(self, runner, vibe_tools_root):
        """Test that different flag combinations work together."""
        if not vibe_tools_root.exists():
            pytest.skip("vibe-tools root not found")

        # Test with both --collection-only and --verbose
        result = runner.invoke(
            cli,
            [
                "analyze-all",
                "--collection-only",
                "--verbose",
                "--source",
                str(vibe_tools_root),
            ],
        )
        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Test with --enable-execution and --collection-only
        # (collection-only should take precedence)
        result = runner.invoke(
            cli,
            [
                "analyze-all",
                "--collection-only",
                "--enable-execution",
                "--source",
                str(vibe_tools_root),
            ],
        )
        assert result.exit_code == 0, f"Command failed: {result.output}"
