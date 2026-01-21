#!/usr/bin/env python3
"""Script to identify and prioritize the top 50 agents from vibe-tools.

This script analyzes all agents, prompts, instructions, and chatmodes
to identify the most valuable ones for the discovery system.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent_discovery.collector import AgentCollector
from agent_discovery.models import AgentType, Category


def main():
    """Collect and analyze agents, outputting top 50 recommendations."""

    # Find vibe-tools root
    vibe_tools = Path(__file__).parent.parent
    if not (vibe_tools / "ghc_tools/agents").exists():
        print(f"Error: Could not find vibe-tools at {vibe_tools}")
        return

    print(f"📂 Scanning vibe-tools at: {vibe_tools}\n")

    # Collect all agents
    collector = AgentCollector(str(vibe_tools))
    agents = collector.collect_all(verbose=True)
    agents = collector.deduplicate(agents)

    print(f"\n📊 Total unique agents: {len(agents)}\n")

    # Get statistics
    stats = collector.get_statistics(agents)

    print("=== By Type ===")
    for t, count in sorted(stats["by_type"].items(), key=lambda x: -x[1]):
        print(f"  {t}: {count}")

    print("\n=== By Category ===")
    for c, count in sorted(stats["by_category"].items(), key=lambda x: -x[1]):
        print(f"  {c}: {count}")

    print("\n=== By Source Collection ===")
    for s, count in sorted(stats["by_collection"].items(), key=lambda x: -x[1]):
        print(f"  {s}: {count}")

    # Score agents by quality indicators
    def score_agent(agent):
        """Score an agent for prioritization."""
        score = 0

        # Has description (+10)
        if agent.description:
            score += 10

        # Has use cases (+5 per case, max 25)
        score += min(len(agent.use_cases) * 5, 25)

        # Has tech stack keywords (+2 per keyword, max 20)
        score += min(len(agent.tech_stack) * 2, 20)

        # Is a core type (agents > chatmodes > prompts > instructions)
        type_scores = {
            AgentType.AGENT: 15,
            AgentType.CHATMODE: 12,
            AgentType.PROMPT: 8,
            AgentType.INSTRUCTION: 5,
        }
        score += type_scores.get(agent.agent_type, 0)

        # High-value categories
        category_scores = {
            Category.ARCHITECTURE: 10,
            Category.TESTING: 10,
            Category.SECURITY: 10,
            Category.DEVOPS: 8,
            Category.BACKEND: 8,
            Category.FRONTEND: 8,
            Category.AI_ML: 8,
            Category.DATABASE: 6,
        }
        score += category_scores.get(agent.category, 0)

        # Bonus for popular frameworks
        popular_frameworks = ["nextjs", "react", "fastapi", "playwright", "typescript"]
        for fw in popular_frameworks:
            if fw in [f.lower() for f in agent.frameworks]:
                score += 3

        return score

    # Score and rank all agents
    scored_agents = [(agent, score_agent(agent)) for agent in agents]
    scored_agents.sort(key=lambda x: -x[1])

    # Get top 50
    print("\n" + "=" * 70)
    print("🏆 TOP 50 PRIORITY AGENTS")
    print("=" * 70 + "\n")

    top_50 = []
    for i, (agent, score) in enumerate(scored_agents[:50], 1):
        print(f"{i:2}. [{score:3}] {agent.name}")
        print(f"      Type: {agent.agent_type.value} | Category: {agent.category.value}")
        if agent.description:
            print(f"      {agent.description[:70]}...")
        print()

        top_50.append(
            {
                "rank": i,
                "name": agent.name,
                "type": agent.agent_type.value,
                "category": agent.category.value,
                "score": score,
                "description": agent.description,
                "tech_stack": agent.tech_stack,
                "source": agent.source_collection,
            }
        )

    # Save to file
    import json

    output_file = Path(__file__).parent / "data" / "top_50_agents.json"
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(top_50, f, indent=2)

    print(f"\n✅ Top 50 agents saved to: {output_file}")

    # Summary by type for top 50
    print("\n=== Top 50 Distribution ===")
    type_counts = {}
    cat_counts = {}
    for agent, _ in scored_agents[:50]:
        t = agent.agent_type.value
        c = agent.category.value
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
