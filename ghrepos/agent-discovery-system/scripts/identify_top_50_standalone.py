#!/usr/bin/env python3
"""Standalone script to identify and prioritize the top 50 agents from vibe-tools.

This script can be run directly without installing the agent-discovery package.
"""

import hashlib
import json
from enum import Enum
from pathlib import Path

import yaml


class AgentType(str, Enum):
    AGENT = "agent"
    PROMPT = "prompt"
    INSTRUCTION = "instruction"
    CHATMODE = "chatmode"


class Category(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    AI_ML = "ai_ml"
    DEVOPS = "devops"
    SECURITY = "security"
    QUALITY = "quality"
    DATABASE = "database"
    PLANNING = "planning"
    DOCUMENTATION = "documentation"
    GENERAL = "general"


# Category classification keywords
CATEGORY_KEYWORDS = {
    Category.FRONTEND: ["frontend", "react", "nextjs", "vue", "ui", "ux", "component", "css"],
    Category.BACKEND: ["backend", "api", "python", "fastapi", "server", "java", "spring"],
    Category.ARCHITECTURE: ["architect", "system", "design", "infrastructure", "pattern"],
    Category.TESTING: ["test", "qa", "quality", "playwright", "debug", "e2e"],
    Category.AI_ML: ["ai", "ml", "data", "engineer", "scientist", "prompt", "llm"],
    Category.DEVOPS: ["devops", "deploy", "cloud", "incident", "performance", "docker", "k8s"],
    Category.SECURITY: ["security", "audit", "vulnerability", "owasp", "auth"],
    Category.QUALITY: ["review", "refactor", "code quality", "best practice", "lint"],
    Category.DATABASE: ["database", "sql", "postgres", "mongo", "graphql", "dba"],
    Category.PLANNING: ["plan", "requirement", "pm", "product", "task", "prd", "epic"],
    Category.DOCUMENTATION: ["doc", "readme", "markdown", "write", "tutorial"],
}

# Tech stack keywords
TECH_KEYWORDS = {
    "frontend": ["nextjs", "next.js", "react", "vue", "angular", "svelte", "tailwind"],
    "backend": ["python", "fastapi", "django", "flask", "express", "nestjs", "java", "spring"],
    "testing": ["playwright", "vitest", "jest", "pytest", "testing", "e2e"],
    "devops": ["docker", "kubernetes", "terraform", "ci/cd", "github actions"],
}


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from content."""
    frontmatter = {}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
            except yaml.YAMLError:
                pass

    return frontmatter, body


def determine_type(filename: str, default: AgentType) -> AgentType:
    """Determine agent type from filename."""
    filename_lower = filename.lower()
    if ".agent." in filename_lower:
        return AgentType.AGENT
    elif ".prompt." in filename_lower:
        return AgentType.PROMPT
    elif ".instructions." in filename_lower:
        return AgentType.INSTRUCTION
    elif ".chatmode." in filename_lower:
        return AgentType.CHATMODE
    return default


def classify_category(filename: str, content: str) -> Category:
    """Classify agent into a category."""
    text = (filename + " " + content).lower()

    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        scores[category] = score

    best = max(scores, key=lambda k: scores[k], default=Category.GENERAL)
    return best if scores.get(best, 0) > 0 else Category.GENERAL


def extract_tech_stack(content: str) -> list[str]:
    """Extract tech stack keywords from content."""
    content_lower = content.lower()
    found = set()

    for _category, keywords in TECH_KEYWORDS.items():
        for keyword in keywords:
            if keyword in content_lower:
                found.add(keyword)

    return sorted(list(found))


def extract_frameworks(content: str) -> list[str]:
    """Extract framework mentions."""
    frameworks = [
        "nextjs",
        "next.js",
        "react",
        "vue",
        "angular",
        "svelte",
        "fastapi",
        "django",
        "flask",
        "express",
        "nestjs",
        "spring",
        "playwright",
        "vitest",
        "jest",
        "pytest",
        "terraform",
    ]
    content_lower = content.lower()
    found = []
    for fw in frameworks:
        if fw in content_lower:
            found.append(fw.replace(".", ""))
    return list(set(found))


def extract_use_cases(content: str) -> list[str]:
    """Extract use cases from content."""
    use_cases = []
    lines = content.split("\n")
    in_use_case_section = False

    for line in lines:
        line_lower = line.lower()
        if "when to activate" in line_lower or "use cases" in line_lower:
            in_use_case_section = True
            continue
        elif in_use_case_section:
            if line.startswith("#"):
                in_use_case_section = False
            elif line.startswith("- "):
                use_cases.append(line[2:].strip())
            elif len(use_cases) >= 5:
                break

    return use_cases[:5]


def collect_agents(vibe_tools_root: Path) -> list[dict]:
    """Collect all agents from vibe-tools."""
    sources = {
        "ghc_tools/agents": ("ghc_agents", AgentType.AGENT),
        "ghc_tools/prompts": ("ghc_prompts", AgentType.PROMPT),
        "ghc_tools/instructions": ("ghc_instructions", AgentType.INSTRUCTION),
        "ghc_tools/chatmodes": ("ghc_chatmodes", AgentType.CHATMODE),
        "SuperAgent-MCP/agents": ("superagent", AgentType.AGENT),
        ".github/agents": ("github_agents", AgentType.AGENT),
    }

    all_agents = []

    for source_dir, (collection_name, default_type) in sources.items():
        source_path = vibe_tools_root / source_dir
        if not source_path.exists():
            print(f"⚠️  Source not found: {source_dir}")
            continue

        files = list(source_path.glob("*.md"))
        print(f"📂 {source_dir}: Found {len(files)} files")

        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8")
                if not content.strip():
                    continue

                frontmatter, body = parse_frontmatter(content)
                filename = file_path.name

                agent_type = determine_type(filename, default_type)
                name = frontmatter.get(
                    "name",
                    filename.replace(".md", "")
                    .replace(".agent", "")
                    .replace(".prompt", "")
                    .replace(".instructions", "")
                    .replace(".chatmode", ""),
                )

                agent = {
                    "name": name,
                    "agent_type": agent_type.value,
                    "description": frontmatter.get("description", "")[:500],
                    "category": classify_category(filename, content).value,
                    "tech_stack": extract_tech_stack(content),
                    "frameworks": extract_frameworks(content),
                    "use_cases": extract_use_cases(content),
                    "source_path": str(file_path),
                    "source_collection": collection_name,
                    "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16],
                }

                all_agents.append(agent)

            except Exception as e:
                print(f"  ⚠️  Error parsing {file_path.name}: {e}")

    return all_agents


def deduplicate(agents: list[dict]) -> list[dict]:
    """Remove duplicate agents based on content hash."""
    seen = set()
    unique = []
    for agent in agents:
        if agent["content_hash"] not in seen:
            seen.add(agent["content_hash"])
            unique.append(agent)
    return unique


def score_agent(agent: dict) -> int:
    """Score an agent for prioritization."""
    score = 0

    # Has description (+10)
    if agent.get("description"):
        score += 10

    # Has use cases (+5 per case, max 25)
    score += min(len(agent.get("use_cases", [])) * 5, 25)

    # Has tech stack keywords (+2 per keyword, max 20)
    score += min(len(agent.get("tech_stack", [])) * 2, 20)

    # Is a core type
    type_scores = {
        "agent": 15,
        "chatmode": 12,
        "prompt": 8,
        "instruction": 5,
    }
    score += type_scores.get(agent.get("agent_type", ""), 0)

    # High-value categories
    category_scores = {
        "architecture": 10,
        "testing": 10,
        "security": 10,
        "devops": 8,
        "backend": 8,
        "frontend": 8,
        "ai_ml": 8,
        "database": 6,
    }
    score += category_scores.get(agent.get("category", ""), 0)

    # Bonus for popular frameworks
    popular_frameworks = ["nextjs", "react", "fastapi", "playwright", "typescript"]
    for fw in popular_frameworks:
        if fw in [f.lower() for f in agent.get("frameworks", [])]:
            score += 3

    return score


def main():
    """Main function to identify top 50 agents."""
    # Find vibe-tools root
    script_dir = Path(__file__).parent
    vibe_tools = script_dir.parent.parent

    if not (vibe_tools / "ghc_tools/agents").exists():
        # Try current directory
        vibe_tools = Path.cwd()
        if not (vibe_tools / "ghc_tools/agents").exists():
            print("Error: Could not find vibe-tools directory")
            return

    print(f"📂 Scanning vibe-tools at: {vibe_tools}\n")

    # Collect all agents
    agents = collect_agents(vibe_tools)
    agents = deduplicate(agents)

    print(f"\n📊 Total unique agents: {len(agents)}\n")

    # Statistics
    by_type = {}
    by_category = {}
    by_collection = {}

    for agent in agents:
        t = agent["agent_type"]
        c = agent["category"]
        s = agent["source_collection"]
        by_type[t] = by_type.get(t, 0) + 1
        by_category[c] = by_category.get(c, 0) + 1
        by_collection[s] = by_collection.get(s, 0) + 1

    print("=== By Type ===")
    for t, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {t}: {count}")

    print("\n=== By Category ===")
    for c, count in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"  {c}: {count}")

    print("\n=== By Source Collection ===")
    for s, count in sorted(by_collection.items(), key=lambda x: -x[1]):
        print(f"  {s}: {count}")

    # Score and rank
    scored = [(agent, score_agent(agent)) for agent in agents]
    scored.sort(key=lambda x: -x[1])

    # Top 50
    print("\n" + "=" * 70)
    print("🏆 TOP 50 PRIORITY AGENTS")
    print("=" * 70 + "\n")

    top_50 = []
    for i, (agent, score) in enumerate(scored[:50], 1):
        print(f"{i:2}. [{score:3}] {agent['name']}")
        print(f"      Type: {agent['agent_type']} | Category: {agent['category']}")
        if agent.get("description"):
            desc = agent["description"][:70]
            print(f"      {desc}{'...' if len(agent['description']) > 70 else ''}")
        print()

        top_50.append(
            {
                "rank": i,
                "name": agent["name"],
                "type": agent["agent_type"],
                "category": agent["category"],
                "score": score,
                "description": agent.get("description", ""),
                "tech_stack": agent.get("tech_stack", []),
                "frameworks": agent.get("frameworks", []),
                "source": agent["source_collection"],
                "source_path": agent["source_path"],
            }
        )

    # Save to file
    output_file = script_dir / "data" / "top_50_agents.json"
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(top_50, f, indent=2)

    print(f"\n✅ Top 50 agents saved to: {output_file}")

    # Summary
    print("\n=== Top 50 Distribution ===")
    type_counts = {}
    cat_counts = {}
    for agent, _ in scored[:50]:
        t = agent["agent_type"]
        c = agent["category"]
        type_counts[t] = type_counts.get(t, 0) + 1
        cat_counts[c] = cat_counts.get(c, 0) + 1

    print("By Type:")
    for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {count}")

    print("\nBy Category:")
    for c, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {c}: {count}")


if __name__ == "__main__":
    main()
