---
type: reference
---

# Output generator - Creates AGENTS.md and related files from discovery results.

This class generates `AGENTS.md` and other related files based on the results of an agent discovery process.

## Configuration Options
- `vibe_tools_root`: (Optional) Path to vibe-tools for copying agent files

## Content Sections
### Generate AGENTS.md
- `matches`: List of matched agents from discovery
- `profile`: Optional codebase profile for context
- `project_name`: Project name for header (default: "Project")
- `include_setup`: Include setup instructions (default: True)

### Generate Instructions.md
- `matches`: List of matched agents
- `profile`: Optional codebase profile

### Generate Chatmode.md
- `matches`: List of matched agents
- `profile`: Optional codebase profile
- `chatmode_name`: Name for the chatmode (default: "project-assistant")

## Output Format / Reports
- AGENTS.md: A markdown file containing a list of recommended AI agents for the project
- instructions.md: A markdown file with project-specific coding guidelines
- chatmode.md: A markdown file defining a custom chat mode for the project

## Success Criteria
- Generated files are written to the specified output directory

[source: src/agent_discovery/generator.py]