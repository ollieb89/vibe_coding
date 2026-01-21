"""Agent Creator - Generate new agents by analyzing patterns from Chroma."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.console import Console

console = Console()


@dataclass
class AgentPattern:
    """Pattern extracted from existing agents."""

    frontmatter_fields: list[str]
    common_sections: list[str]
    code_example_count: int
    avg_length: int
    vocabulary: set[str]


@dataclass
class GeneratedAgent:
    """A newly generated agent."""

    name: str
    agent_type: str  # agent, instruction, prompt, chatmode
    content: str
    source_agents: list[str]  # agents used as references
    domain_vocabulary: set[str]


class AgentCreator:
    """Create new agents by learning from existing ones in Chroma."""

    def __init__(self, collection_name: str = "agents_discovery"):
        """Initialize the creator with Chroma connection."""
        self.collection_name = collection_name
        self._client = None
        self._collection = None

    @property
    def client(self):
        """Lazy-load Chroma client."""
        if self._client is None:
            import chromadb

            self._client = chromadb.HttpClient(host="localhost", port=9500)
        return self._client

    @property
    def collection(self):
        """Get or create the collection."""
        if self._collection is None:
            self._collection = self.client.get_collection(self.collection_name)
        return self._collection

    def analyze_patterns(self, query: str, n_samples: int = 10) -> AgentPattern:
        """Analyze structural patterns from agents matching a query.

        Args:
            query: Search query to find relevant agents
            n_samples: Number of agents to analyze

        Returns:
            AgentPattern with common structures found
        """
        # Query Chroma for similar agents
        results = self.collection.query(
            query_texts=[query], n_results=n_samples, include=["documents", "metadatas"]
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        # Analyze patterns
        sections: dict[str, int] = {}
        frontmatter_fields: set[str] = set()
        vocabulary: set[str] = set()
        total_length = 0
        code_blocks = 0

        for doc, meta in zip(documents, metadatas, strict=False):
            total_length += len(doc)

            # Count code blocks
            code_blocks += doc.count("```")

            # Extract sections (## headers)
            for line in doc.split("\n"):
                if line.startswith("## "):
                    section = line[3:].strip()
                    sections[section] = sections.get(section, 0) + 1
                elif line.startswith("### "):
                    section = line[4:].strip()
                    sections[section] = sections.get(section, 0) + 1

            # Extract vocabulary (simple word extraction)
            words = set(doc.lower().split())
            vocabulary.update(words)

            # Check for frontmatter fields
            if doc.startswith("---"):
                fm_end = doc.find("---", 3)
                if fm_end > 0:
                    fm = doc[3:fm_end]
                    for line in fm.split("\n"):
                        if ":" in line:
                            field = line.split(":")[0].strip()
                            frontmatter_fields.add(field)

        # Find common sections (appear in >30% of samples)
        threshold = n_samples * 0.3
        common_sections = [s for s, count in sections.items() if count >= threshold]

        return AgentPattern(
            frontmatter_fields=list(frontmatter_fields),
            common_sections=sorted(common_sections, key=lambda s: sections[s], reverse=True),
            code_example_count=code_blocks // (2 * n_samples) if n_samples else 0,
            avg_length=total_length // n_samples if n_samples else 0,
            vocabulary=vocabulary,
        )

    def get_domain_context(self, domain: str, n_results: int = 5) -> dict[str, Any]:
        """Get relevant content from Chroma for a domain.

        Args:
            domain: The domain to search for
            n_results: Number of results to return

        Returns:
            Dictionary with relevant agents and their content
        """
        results = self.collection.query(
            query_texts=[domain],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        agents = []
        for i, (doc, meta, dist) in enumerate(
            zip(
                results.get("documents", [[]])[0],
                results.get("metadatas", [[]])[0],
                results.get("distances", [[]])[0],
                strict=False,
            )
        ):
            agents.append(
                {
                    "name": meta.get("name", f"agent_{i}"),
                    "type": meta.get("agent_type", "unknown"),
                    "description": meta.get("description", ""),
                    "content_preview": doc[:500] if doc else "",
                    "relevance": round((1 - dist) * 100),
                }
            )

        return {
            "domain": domain,
            "related_agents": agents,
            "total_found": len(agents),
        }

    def extract_vocabulary(self, domain: str, n_samples: int = 10) -> set[str]:
        """Extract domain-specific vocabulary from related agents.

        Args:
            domain: The domain to search for
            n_samples: Number of agents to sample

        Returns:
            Set of relevant domain terms
        """
        results = self.collection.query(
            query_texts=[domain], n_results=n_samples, include=["documents"]
        )

        documents = results.get("documents", [[]])[0]

        # Extract meaningful terms (filter common words)
        common_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "and",
            "or",
            "but",
            "if",
            "then",
            "else",
            "when",
            "where",
            "what",
            "which",
            "who",
            "how",
            "why",
            "this",
            "that",
            "these",
            "those",
            "it",
            "its",
            "for",
            "to",
            "from",
            "by",
            "with",
            "at",
            "in",
            "on",
            "of",
            "as",
            "not",
            "no",
            "yes",
            "all",
            "any",
            "each",
            "every",
            "both",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "than",
            "too",
            "very",
            "just",
            "also",
            "only",
            "-",
            "##",
            "###",
            "```",
            "---",
            "|",
            "you",
            "your",
            "use",
        }

        vocabulary: dict[str, int] = {}
        for doc in documents:
            words = doc.lower().split()
            for word in words:
                # Clean word
                word = word.strip(".,;:!?\"'()[]{}<>*/\\|`#-_")
                if len(word) > 2 and word not in common_words and word.isalpha():
                    vocabulary[word] = vocabulary.get(word, 0) + 1

        # Return top terms (appear more than once)
        return {w for w, c in vocabulary.items() if c > 1}

    def generate_agent_prompt(
        self,
        domain: str,
        agent_type: str = "agent",
        include_examples: bool = True,
    ) -> str:
        """Generate a prompt for creating a new agent.

        This creates a detailed prompt that can be used with an LLM
        to generate the actual agent content.

        Args:
            domain: The domain/topic for the new agent
            agent_type: Type of agent (agent, instruction, prompt, chatmode)
            include_examples: Whether to include example content from Chroma

        Returns:
            A prompt string for generating the agent
        """
        # Get context from Chroma
        context = self.get_domain_context(domain, n_results=5)
        patterns = self.analyze_patterns(domain, n_samples=10)
        vocabulary = self.extract_vocabulary(domain, n_samples=10)

        # Build the prompt
        prompt_parts = [
            f"# Task: Create a {agent_type} for {domain}",
            "",
            "## Context from Existing Agents",
            "",
            f"Found {context['total_found']} related agents:",
        ]

        for agent in context["related_agents"]:
            prompt_parts.append(
                f"- **{agent['name']}** ({agent['relevance']}% relevance): {agent['description']}"
            )

        prompt_parts.extend(
            [
                "",
                "## Structural Patterns to Follow",
                "",
                f"**Frontmatter fields**: {', '.join(patterns.frontmatter_fields)}",
                f"**Common sections**: {', '.join(patterns.common_sections[:10])}",
                f"**Target length**: ~{patterns.avg_length} characters",
                f"**Code examples**: Include {patterns.code_example_count} code blocks",
                "",
                "## Domain Vocabulary to Include",
                "",
                "Use these terms naturally throughout the agent:",
                ", ".join(sorted(list(vocabulary)[:50])),
                "",
                "## Generation Instructions",
                "",
                f"1. Create a comprehensive {agent_type} file for {domain}",
                "2. Follow the structural patterns from existing agents",
                "3. Include dense domain-specific vocabulary for semantic search",
                "4. Add practical code examples",
                "5. Use clear section headers",
                "",
            ]
        )

        if include_examples and context["related_agents"]:
            prompt_parts.extend(
                [
                    "## Example Content from Top Match",
                    "",
                    "```",
                    context["related_agents"][0]["content_preview"],
                    "...",
                    "```",
                ]
            )

        return "\n".join(prompt_parts)

    def generate_agent_template(
        self,
        domain: str,
        agent_type: str = "agent",
        name: str | None = None,
    ) -> str:
        """Generate a template for a new agent with placeholders.

        Args:
            domain: The domain/topic for the new agent
            agent_type: Type of agent (agent, instruction, prompt, chatmode)
            name: Optional custom name for the agent

        Returns:
            Template string with structure and placeholders
        """
        # Get patterns from existing agents
        patterns = self.analyze_patterns(domain, n_samples=10)
        vocabulary = self.extract_vocabulary(domain, n_samples=10)

        # Generate name
        agent_name = name or domain.lower().replace(" ", "-")

        # Build template based on agent type
        if agent_type == "agent":
            return self._agent_template(agent_name, domain, patterns, vocabulary)
        elif agent_type == "instruction":
            return self._instruction_template(agent_name, domain, patterns, vocabulary)
        elif agent_type == "prompt":
            return self._prompt_template(agent_name, domain, patterns, vocabulary)
        elif agent_type == "chatmode":
            return self._chatmode_template(agent_name, domain, patterns, vocabulary)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

    def _agent_template(
        self,
        name: str,
        domain: str,
        patterns: AgentPattern,
        vocabulary: set[str],
    ) -> str:
        """Generate agent template."""
        vocab_list = ", ".join(sorted(list(vocabulary)[:20]))

        return f"""---
description: '{domain.title()} expert specializing in [SPECIFIC AREAS]'
---

# {domain.title()} Agent

You are an expert {domain} specialist with deep knowledge of [KEY TECHNOLOGIES].

## Core Expertise

### [Primary Area]
- [Key skill 1]
- [Key skill 2]
- [Key skill 3]

### [Secondary Area]
- [Key skill 1]
- [Key skill 2]

## Key Vocabulary

This agent should be proficient in: {vocab_list}

## Code Examples

```[language]
# Example 1: [Description]
[code]
```

```[language]
# Example 2: [Description]
[code]
```

## Best Practices

1. [Practice 1]
2. [Practice 2]
3. [Practice 3]

## Workflow

1. [Step 1]
2. [Step 2]
3. [Step 3]

## Related Resources

- **Instructions**: `ghc_tools/instructions/{name}.instructions.md`
- **Prompts**: `ghc_tools/prompts/{name}-*.prompt.md`
"""

    def _instruction_template(
        self,
        name: str,
        domain: str,
        patterns: AgentPattern,
        vocabulary: set[str],
    ) -> str:
        """Generate instruction template."""
        return f"""---
description: '{domain.title()} coding guidelines and best practices'
applyTo: '**/*.[relevant-extensions]'
---

# {domain.title()} Guidelines

## Overview

These instructions provide guidelines for {domain} development.

## Code Style

### [Category 1]

```[language]
// ✅ Good
[good example]

// ❌ Bad
[bad example]
```

### [Category 2]

```[language]
// ✅ Good
[good example]

// ❌ Bad
[bad example]
```

## Patterns

### [Pattern 1]

[Description and example]

### [Pattern 2]

[Description and example]

## Anti-Patterns

❌ [Anti-pattern 1]
❌ [Anti-pattern 2]
❌ [Anti-pattern 3]

✅ [Correct approach 1]
✅ [Correct approach 2]
✅ [Correct approach 3]

## Testing

[Testing guidelines]

## Security

[Security considerations]
"""

    def _prompt_template(
        self,
        name: str,
        domain: str,
        patterns: AgentPattern,
        vocabulary: set[str],
    ) -> str:
        """Generate prompt template."""
        return f"""---
description: '{domain.title()} workflow - [specific task description]'
---

# {domain.title()} Prompt

[Brief description of what this prompt accomplishes]

## Input Requirements

Provide the following:
- **[Input 1]**: [Description]
- **[Input 2]**: [Description]
- **[Input 3]**: [Description]

## Workflow

### Step 1: [First Step]

[Description]

```[language]
[example]
```

### Step 2: [Second Step]

[Description]

### Step 3: [Third Step]

[Description]

## Output

[What the prompt produces]

## Example Usage

```
@prompt ghc_tools/prompts/{name}.prompt.md
[Input 1]: [example value]
[Input 2]: [example value]
```

## Related Resources

- **Agent**: `ghc_tools/agents/{name}.agent.md`
- **Instructions**: `ghc_tools/instructions/{name}.instructions.md`
"""

    def _chatmode_template(
        self,
        name: str,
        domain: str,
        patterns: AgentPattern,
        vocabulary: set[str],
    ) -> str:
        """Generate chatmode template."""
        return f"""---
description: '{domain.title()} chat mode - interactive {domain} assistance'
tools: ['codebase', 'editFiles', 'fetch', 'problems', 'runCommands', 'search', 'usages']
---

# {domain.title()} Chat Mode

You are a {domain} specialist assistant.

## Agent Profile

- **Agent File**: `ghc_tools/agents/{name}.agent.md`
- **Expertise**: [List key areas]
- **Focus**: [Primary focus]

## Core Behaviors

### 1. [Behavior Category 1]
- [Behavior description]
- [Behavior description]

### 2. [Behavior Category 2]
- [Behavior description]
- [Behavior description]

## Available Resources

### Instructions
```
ghc_tools/instructions/{name}.instructions.md
```

### Prompts
```
@prompt ghc_tools/prompts/{name}-[task].prompt.md
```

## Interaction Patterns

### When Asked About [Topic 1]
1. [Step 1]
2. [Step 2]
3. [Step 3]

### When Asked About [Topic 2]
1. [Step 1]
2. [Step 2]

## Communication Style

- [Style guideline 1]
- [Style guideline 2]
- [Style guideline 3]
"""

    def save_agent(
        self,
        content: str,
        name: str,
        agent_type: str,
        output_dir: str | Path,
    ) -> Path:
        """Save generated agent to file.

        Args:
            content: Agent content
            name: Agent name (without extension)
            agent_type: Type for determining subdirectory
            output_dir: Base output directory

        Returns:
            Path to saved file
        """
        output_dir = Path(output_dir)

        # Determine subdirectory and extension
        type_config = {
            "agent": ("agents", ".agent.md"),
            "instruction": ("instructions", ".instructions.md"),
            "prompt": ("prompts", ".prompt.md"),
            "chatmode": ("chatmodes", ".chatmode.md"),
        }

        subdir, ext = type_config.get(agent_type, ("agents", ".agent.md"))

        # Create output path
        output_path = output_dir / subdir / f"{name}{ext}"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        output_path.write_text(content)

        return output_path
