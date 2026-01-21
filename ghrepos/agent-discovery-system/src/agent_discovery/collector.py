"""Agent collector - Scans and normalizes agents from all vibe-tools sources."""

import glob
import hashlib
import os
from pathlib import Path

import yaml

from agent_discovery.models import Agent, AgentType, Category, Complexity


class AgentCollector:
    """Collects and normalizes agents from all vibe-tools sources."""

    # Source directories relative to vibe-tools root
    SOURCES: dict[str, tuple[str, AgentType]] = {
        "ghc_tools/agents": ("ghc_agents", AgentType.AGENT),
        "ghc_tools/prompts": ("ghc_prompts", AgentType.PROMPT),
        "ghc_tools/instructions": ("ghc_instructions", AgentType.INSTRUCTION),
        "ghc_tools/chatmodes": ("ghc_chatmodes", AgentType.CHATMODE),
        "SuperAgent-MCP/agents": ("superagent", AgentType.AGENT),
        ".github/agents": ("github_agents", AgentType.AGENT),
        "copilot-orchestra": ("copilot_orchestra", AgentType.AGENT),
        "SuperClaude_Framework": ("superclaudefw", AgentType.AGENT),
        "SuperFlag_Framework": ("superflagsfw", AgentType.AGENT),
    }

    # Tech stack keywords for extraction
    TECH_KEYWORDS: dict[str, list[str]] = {
        "frontend": [
            "nextjs",
            "next.js",
            "react",
            "vue",
            "angular",
            "svelte",
            "astro",
            "typescript",
            "tailwind",
            "css",
            "html",
            "ui",
            "ux",
            "shadcn",
        ],
        "backend": [
            "python",
            "fastapi",
            "django",
            "flask",
            "express",
            "nestjs",
            "api",
            "rest",
            "graphql",
            "websocket",
            "middleware",
            "java",
            "spring",
            "springboot",
            "kotlin",
            "go",
            "rust",
            "node",
            "nodejs",
        ],
        "database": [
            "postgresql",
            "postgres",
            "sql",
            "mysql",
            "mongodb",
            "redis",
            "prisma",
            "sqlalchemy",
            "drizzle",
            "neon",
            "supabase",
            "warehouse",
            "data lake",
            "lakehouse",
            "analytics",
            "snowflake",
            "bigquery",
            "redshift",
            "duckdb",
            "spark",
            "pyspark",
            "databricks",
            "airflow",
            "dagster",
            "dbt",
            "mlflow",
        ],
        "testing": [
            "playwright",
            "vitest",
            "jest",
            "pytest",
            "testing",
            "test",
            "e2e",
            "unit",
            "integration",
            "tdd",
            "bdd",
        ],
        "ai_ml": [
            "ai",
            "ml",
            "machine learning",
            "llm",
            "embeddings",
            "vector",
            "rag",
            "prompt",
            "openai",
            "anthropic",
            "langchain",
            "copilot",
        ],
        "devops": [
            "docker",
            "kubernetes",
            "k8s",
            "terraform",
            "ansible",
            "ci/cd",
            "github actions",
            "azure devops",
            "vercel",
            "railway",
            "aws",
        ],
        "security": [
            "security",
            "auth",
            "authentication",
            "authorization",
            "jwt",
            "oauth",
            "owasp",
            "vulnerability",
            "encryption",
        ],
    }

    # Category classification keywords
    CATEGORY_KEYWORDS: dict[Category, list[str]] = {
        Category.FRONTEND: ["frontend", "react", "nextjs", "vue", "ui", "ux", "component", "css"],
        Category.BACKEND: ["backend", "api", "python", "fastapi", "server", "java", "spring"],
        Category.ARCHITECTURE: ["architect", "system", "design", "infrastructure", "pattern"],
        Category.TESTING: ["test", "qa", "quality", "playwright", "debug", "e2e"],
        Category.AI_ML: ["ai", "ml", "data", "engineer", "scientist", "prompt", "llm"],
        Category.DEVOPS: ["devops", "deploy", "cloud", "incident", "performance", "docker", "k8s"],
        Category.SECURITY: ["security", "audit", "vulnerability", "owasp", "auth"],
        Category.QUALITY: ["review", "refactor", "code quality", "best practice", "lint"],
        Category.DATABASE: [
            "database",
            "sql",
            "postgres",
            "mongo",
            "graphql",
            "dba",
            "analytics",
            "warehouse",
            "etl",
            "pipeline",
            "spark",
            "airflow",
            "dbt",
            "pandas",
            "numpy",
        ],
        Category.PLANNING: ["plan", "requirement", "pm", "product", "task", "prd", "epic"],
        Category.DOCUMENTATION: ["doc", "readme", "markdown", "write", "tutorial"],
    }

    def __init__(self, vibe_tools_root: str):
        """Initialize collector with vibe-tools root path.

        Args:
            vibe_tools_root: Absolute path to vibe-tools directory
        """
        self.root = Path(vibe_tools_root)
        if not self.root.exists():
            raise ValueError(f"vibe-tools root not found: {vibe_tools_root}")

    def collect_all(self, verbose: bool = True) -> list[Agent]:
        """Collect all agents from all sources.

        Args:
            verbose: Print progress messages

        Returns:
            List of collected Agent objects
        """
        all_agents: list[Agent] = []

        for source_dir, (collection_name, agent_type) in self.SOURCES.items():
            source_path = self.root / source_dir
            if not source_path.exists():
                if verbose:
                    print(f"⚠️  Source not found: {source_dir}")
                continue

            agents = self._collect_from_directory(source_path, collection_name, agent_type, verbose)
            all_agents.extend(agents)

        if verbose:
            print(f"\n✅ Collected {len(all_agents)} total agents")

        return all_agents

    def _collect_from_directory(
        self,
        directory: Path,
        collection_name: str,
        agent_type: AgentType,
        verbose: bool,
    ) -> list[Agent]:
        """Collect agents from a single directory.

        Args:
            directory: Path to scan
            collection_name: Name of source collection
            agent_type: Default type for agents in this directory
            verbose: Print progress

        Returns:
            List of agents from this directory
        """
        agents: list[Agent] = []
        patterns = ["*.md", "*.agent.md", "*.prompt.md", "*.instructions.md", "*.chatmode.md"]

        files: list[str] = []
        for pattern in patterns:
            files.extend(glob.glob(str(directory / pattern)))

        if verbose:
            print(f"📂 {directory.name}: Found {len(files)} files")

        for file_path in files:
            try:
                agent = self._parse_agent_file(file_path, collection_name, agent_type)
                if agent:
                    agents.append(agent)
            except Exception as e:
                if verbose:
                    print(f"  ⚠️  Error parsing {os.path.basename(file_path)}: {e}")

        return agents

    def _parse_agent_file(
        self,
        file_path: str,
        collection_name: str,
        default_type: AgentType,
    ) -> Agent | None:
        """Parse a single agent file.

        Args:
            file_path: Path to agent file
            collection_name: Source collection name
            default_type: Default agent type

        Returns:
            Parsed Agent object or None if invalid
        """
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            return None

        # Parse frontmatter
        frontmatter, body = self._parse_frontmatter(content)

        # Determine agent type from filename
        filename = os.path.basename(file_path)
        agent_type = self._determine_type(filename, default_type)

        # Extract agent name
        name = frontmatter.get(
            "name",
            filename.replace(".md", "")
            .replace(".agent", "")
            .replace(".prompt", "")
            .replace(".instructions", "")
            .replace(".chatmode", ""),
        )

        # Extract metadata
        tech_stack = self._extract_tech_stack(content)
        languages = self._extract_languages(content)
        frameworks = self._extract_frameworks(content)
        category = self._classify_category(filename, content)
        use_cases = self._extract_use_cases(content)
        complexity = self._estimate_complexity(content)
        subjects = self._extract_subjects(content, category)

        # Create content hash for deduplication
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        return Agent(
            name=name,
            agent_type=agent_type,
            description=frontmatter.get("description", "")[:500],
            category=category,
            tech_stack=tech_stack,
            languages=languages,
            frameworks=frameworks,
            use_cases=use_cases,
            complexity=complexity,
            subjects=subjects,
            source_path=file_path,
            source_collection=collection_name,
            content=content,
            content_hash=content_hash,
            frontmatter=frontmatter,
        )

    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """Parse YAML frontmatter from content.

        Args:
            content: Full file content

        Returns:
            Tuple of (frontmatter_dict, remaining_content)
        """
        frontmatter: dict = {}
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

    def _determine_type(self, filename: str, default: AgentType) -> AgentType:
        """Determine agent type from filename.

        Args:
            filename: File name
            default: Default type if not determinable

        Returns:
            AgentType enum value
        """
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

    def _extract_tech_stack(self, content: str) -> list[str]:
        """Extract tech stack keywords from content.

        Args:
            content: File content

        Returns:
            List of tech keywords found
        """
        content_lower = content.lower()
        found: set[str] = set()

        for _category, keywords in self.TECH_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content_lower:
                    found.add(keyword)

        return sorted(found)

    def _extract_languages(self, content: str) -> list[str]:
        """Extract programming language mentions.

        Args:
            content: File content

        Returns:
            List of programming languages found
        """
        languages = [
            "python",
            "typescript",
            "javascript",
            "java",
            "kotlin",
            "go",
            "rust",
            "c#",
            "csharp",
            "ruby",
            "php",
            "swift",
            "sql",
        ]
        content_lower = content.lower()
        return [lang for lang in languages if lang in content_lower]

    def _extract_frameworks(self, content: str) -> list[str]:
        """Extract framework mentions.

        Args:
            content: File content

        Returns:
            List of frameworks found
        """
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
                # Normalize next.js -> nextjs
                found.append(fw.replace(".", ""))
        return list(set(found))

    def _classify_category(self, filename: str, content: str) -> Category:
        """Classify agent into a category.

        Args:
            filename: Agent filename
            content: File content

        Returns:
            Category enum value
        """
        text = (filename + " " + content).lower()

        scores: dict[Category, int] = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[category] = score

        # Return highest scoring category
        best = max(scores, key=lambda k: scores[k], default=Category.GENERAL)
        return best if scores.get(best, 0) > 0 else Category.GENERAL

    def _extract_use_cases(self, content: str) -> list[str]:
        """Extract use cases from content.

        Args:
            content: File content

        Returns:
            List of use case descriptions
        """
        use_cases: list[str] = []

        # Look for "When to activate" or "Use cases" sections
        lines = content.split("\n")
        in_use_case_section = False

        for line in lines:
            line_lower = line.lower()
            if "when to activate" in line_lower or "use cases" in line_lower:
                in_use_case_section = True
                continue
            elif in_use_case_section:
                if line.startswith("#"):  # New section
                    in_use_case_section = False
                elif line.startswith("- "):
                    use_cases.append(line[2:].strip())
                elif not line.strip():
                    continue
                elif len(use_cases) >= 5:  # Limit extraction
                    break

        return use_cases[:5]

    def _estimate_complexity(self, content: str) -> Complexity:
        """Estimate agent complexity based on content.

        Args:
            content: File content

        Returns:
            Complexity level
        """
        content_lower = content.lower()

        # Advanced indicators
        advanced_keywords = [
            "architecture",
            "microservice",
            "distributed",
            "scale",
            "security",
            "compliance",
            "enterprise",
            "optimization",
        ]
        advanced_count = sum(1 for kw in advanced_keywords if kw in content_lower)

        # Beginner indicators
        beginner_keywords = [
            "basic",
            "simple",
            "beginner",
            "introduction",
            "starter",
            "getting started",
            "tutorial",
        ]
        beginner_count = sum(1 for kw in beginner_keywords if kw in content_lower)

        if advanced_count >= 3:
            return Complexity.ADVANCED
        elif beginner_count >= 2:
            return Complexity.BEGINNER
        return Complexity.INTERMEDIATE

    def _extract_subjects(self, content: str, category: Category) -> list[str]:
        """Extract subject tags for leaderboard grouping.

        Args:
            content: File content
            category: Already-classified category

        Returns:
            List of subject tags (e.g., security, testing, infra)
        """
        # Start with the primary category as a subject
        subjects: set[str] = {category.value}
        content_lower = content.lower()

        # Subject keyword mapping (broader than category)
        subject_keywords: dict[str, list[str]] = {
            "security": [
                "security",
                "auth",
                "owasp",
                "vulnerability",
                "jwt",
                "oauth",
                "encryption",
            ],
            "testing": ["test", "playwright", "vitest", "pytest", "e2e", "qa", "quality"],
            "infra": [
                "docker",
                "kubernetes",
                "k8s",
                "terraform",
                "aws",
                "cloud",
                "devops",
                "ci/cd",
            ],
            "frontend": ["react", "nextjs", "vue", "angular", "css", "ui", "ux", "component"],
            "backend": ["api", "fastapi", "django", "express", "server", "python", "java"],
            "ai": ["ai", "ml", "llm", "prompt", "embeddings", "rag", "langchain", "openai"],
            "database": [
                "sql",
                "postgres",
                "mongodb",
                "redis",
                "prisma",
                "database",
                "warehouse",
                "analytics",
                "snowflake",
                "bigquery",
                "redshift",
            ],
            "data-science": [
                "data science",
                "analytics",
                "pandas",
                "numpy",
                "scikit-learn",
                "sklearn",
                "spark",
                "pyspark",
                "dbt",
                "airflow",
                "dagster",
                "feature store",
                "mlflow",
                "lakehouse",
            ],
            "architecture": ["architect", "system design", "pattern", "microservice", "scale"],
            "documentation": ["doc", "readme", "markdown", "tutorial", "guide"],
        }

        for subject, keywords in subject_keywords.items():
            if any(kw in content_lower for kw in keywords):
                subjects.add(subject)

        return sorted(subjects)

    def deduplicate(self, agents: list[Agent]) -> list[Agent]:
        """Remove duplicate agents based on content hash.

        Args:
            agents: List of agents to deduplicate

        Returns:
            Deduplicated list (keeps first occurrence)
        """
        seen_hashes: set[str] = set()
        unique: list[Agent] = []

        for agent in agents:
            if agent.content_hash not in seen_hashes:
                seen_hashes.add(agent.content_hash)
                unique.append(agent)

        return unique

    def get_statistics(self, agents: list[Agent]) -> dict:
        """Generate statistics about collected agents.

        Args:
            agents: List of agents

        Returns:
            Dictionary of statistics
        """
        stats = {
            "total": len(agents),
            "by_type": {},
            "by_category": {},
            "by_collection": {},
            "languages": set(),
            "frameworks": set(),
        }

        for agent in agents:
            # Count by type
            type_name = agent.agent_type.value
            stats["by_type"][type_name] = stats["by_type"].get(type_name, 0) + 1

            # Count by category
            cat_name = agent.category.value
            stats["by_category"][cat_name] = stats["by_category"].get(cat_name, 0) + 1

            # Count by collection
            coll = agent.source_collection
            stats["by_collection"][coll] = stats["by_collection"].get(coll, 0) + 1

            # Collect languages and frameworks
            stats["languages"].update(agent.languages)
            stats["frameworks"].update(agent.frameworks)

        # Convert sets to sorted lists
        stats["languages"] = sorted(stats["languages"])
        stats["frameworks"] = sorted(stats["frameworks"])

        return stats
