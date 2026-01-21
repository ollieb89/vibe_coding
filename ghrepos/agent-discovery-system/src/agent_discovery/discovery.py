"""Discovery engine - Semantic search and agent recommendation."""

import json
from pathlib import Path
from typing import Any

from agent_discovery.ingester import AgentRetriever
from agent_discovery.models import (
    AgentMatch,
    Category,
    CodebaseProfile,
    SearchCriteria,
)
from agent_discovery.questions import QuestionGenerator, get_category_for_need


class DiscoveryEngine:
    """Main engine for discovering and recommending agents."""

    def __init__(self, collection_name: str = "agents_discovery"):
        """Initialize discovery engine.

        Args:
            collection_name: Chroma collection to query
        """
        self.retriever = AgentRetriever(collection_name)
        self.question_generator = QuestionGenerator()

    def analyze_codebase(self, path: str) -> CodebaseProfile:
        """Analyze a codebase to detect languages, frameworks, and patterns.

        Args:
            path: Path to codebase root

        Returns:
            CodebaseProfile with detected attributes
        """
        root = Path(path).resolve()
        if not root.exists():
            raise ValueError(f"Path does not exist: {path}")

        profile = CodebaseProfile(path=str(root))

        # Count files by extension
        file_types: dict[str, int] = {}
        file_count = 0

        for ext in ["py", "ts", "tsx", "js", "jsx", "java", "go", "rs", "rb", "php", "cs"]:
            files = list(root.glob(f"**/*.{ext}"))
            # Exclude node_modules, venv, etc.
            files = [f for f in files if not self._should_exclude(f)]
            if files:
                file_types[f".{ext}"] = len(files)
                file_count += len(files)

        profile.file_types = file_types
        profile.file_count = file_count

        # Detect languages from file types
        profile.languages = self._detect_languages(file_types)

        # Analyze package files for dependencies
        profile.dependencies, profile.dev_dependencies = self._analyze_dependencies(root)

        # Detect frameworks
        profile.frameworks = self._detect_frameworks(profile.dependencies, root)

        # Detect patterns
        profile.patterns = self._detect_patterns(root)

        # Check for tests, CI, Docker
        profile.has_tests = any(
            [
                (root / "tests").exists(),
                (root / "test").exists(),
                (root / "__tests__").exists(),
                list(root.glob("**/*.test.*")),
                list(root.glob("**/*.spec.*")),
            ]
        )
        profile.has_ci = any(
            [
                (root / ".github/workflows").exists(),
                (root / ".gitlab-ci.yml").exists(),
                (root / "azure-pipelines.yml").exists(),
            ]
        )
        profile.has_docker = any(
            [
                (root / "Dockerfile").exists(),
                (root / "docker-compose.yml").exists(),
                (root / "docker-compose.yaml").exists(),
            ]
        )

        return profile

    def _should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded from analysis.

        Args:
            path: Path to check

        Returns:
            True if should be excluded
        """
        exclude_dirs = {
            "node_modules",
            "venv",
            ".venv",
            "env",
            ".env",
            "__pycache__",
            ".git",
            "dist",
            "build",
            ".next",
            "target",
            "vendor",
            ".idea",
            ".vscode",
        }
        parts = set(path.parts)
        return bool(parts & exclude_dirs)

    def _detect_languages(self, file_types: dict[str, int]) -> list[str]:
        """Detect programming languages from file types.

        Args:
            file_types: Dictionary of extension -> count

        Returns:
            List of detected languages
        """
        ext_to_lang = {
            ".py": "python",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".java": "java",
            ".kt": "kotlin",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".cs": "csharp",
        }
        languages: set[str] = set()
        for ext, count in file_types.items():
            if count > 0 and ext in ext_to_lang:
                languages.add(ext_to_lang[ext])
        return sorted(languages)

    def _analyze_dependencies(self, root: Path) -> tuple[list[str], list[str]]:
        """Analyze package files for dependencies.

        Args:
            root: Codebase root path

        Returns:
            Tuple of (dependencies, dev_dependencies)
        """
        deps: list[str] = []
        dev_deps: list[str] = []

        # package.json (Node.js)
        package_json = root / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    pkg = json.load(f)
                deps.extend(pkg.get("dependencies", {}).keys())
                dev_deps.extend(pkg.get("devDependencies", {}).keys())
            except (json.JSONDecodeError, OSError):
                pass

        # pyproject.toml (Python)
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib

                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                project_deps = data.get("project", {}).get("dependencies", [])
                # Extract package names from dependency specs
                for dep in project_deps:
                    name = dep.split("[")[0].split(">=")[0].split("==")[0].split("<")[0].strip()
                    deps.append(name)
            except Exception:
                pass

        # requirements.txt (Python)
        requirements = root / "requirements.txt"
        if requirements.exists():
            try:
                with open(requirements) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            name = line.split("==")[0].split(">=")[0].split("[")[0].strip()
                            deps.append(name)
            except OSError:
                pass

        return list(set(deps)), list(set(dev_deps))

    def _detect_frameworks(
        self,
        dependencies: list[str],
        root: Path,
    ) -> list[str]:
        """Detect frameworks from dependencies and file structure.

        Args:
            dependencies: List of package dependencies
            root: Codebase root path

        Returns:
            List of detected frameworks
        """
        frameworks: set[str] = set()

        # Framework indicators in dependencies
        framework_deps = {
            "next": "nextjs",
            "react": "react",
            "vue": "vue",
            "@angular/core": "angular",
            "svelte": "svelte",
            "astro": "astro",
            "fastapi": "fastapi",
            "django": "django",
            "flask": "flask",
            "express": "express",
            "@nestjs/core": "nestjs",
            "spring-boot": "spring",
            "playwright": "playwright",
            "vitest": "vitest",
            "jest": "jest",
            "pytest": "pytest",
        }

        deps_lower = [d.lower() for d in dependencies]
        for dep, framework in framework_deps.items():
            if dep.lower() in deps_lower:
                frameworks.add(framework)

        # File structure indicators
        if (root / "next.config.js").exists() or (root / "next.config.ts").exists():
            frameworks.add("nextjs")
        if (root / "tailwind.config.js").exists() or (root / "tailwind.config.ts").exists():
            frameworks.add("tailwind")
        if (root / "playwright.config.ts").exists():
            frameworks.add("playwright")

        return sorted(frameworks)

    def _detect_patterns(self, root: Path) -> list[str]:
        """Detect architectural patterns and practices.

        Args:
            root: Codebase root path

        Returns:
            List of detected patterns
        """
        patterns: set[str] = set()

        # Directory-based patterns
        if (root / "app").exists() or (root / "src/app").exists():
            patterns.add("app-router")
        if (root / "pages").exists() or (root / "src/pages").exists():
            patterns.add("pages-router")
        if (root / "components").exists() or (root / "src/components").exists():
            patterns.add("component-based")
        if (root / "api").exists() or (root / "src/api").exists():
            patterns.add("api-routes")
        if (root / "lib").exists() or (root / "src/lib").exists():
            patterns.add("library-pattern")

        # File patterns
        if list(root.glob("**/*.controller.*")):
            patterns.add("mvc")
        if list(root.glob("**/*.service.*")):
            patterns.add("service-layer")
        if list(root.glob("**/*.repository.*")):
            patterns.add("repository-pattern")

        return sorted(patterns)

    def discover(
        self,
        criteria: SearchCriteria,
        n_results: int = 10,
        min_score: float | None = None,
        subject_top_n: dict[str, int] | None = None,
    ) -> list[AgentMatch]:
        """Discover agents matching the search criteria.

        Args:
            criteria: Search criteria from user input
            n_results: Number of results to return
            min_score: Minimum score required for a match (0-1)
            subject_top_n: Optional per-subject caps, e.g. {"database": 3}

        Returns:
            List of AgentMatch objects ranked by relevance
        """
        # Build search query from criteria
        query = self.question_generator.build_search_query(criteria)

        # Build metadata filter
        where_filter = self._build_filter(criteria)

        # Perform semantic search
        results = self.retriever.search(
            query=query,
            n_results=n_results * 2,  # Over-fetch for ranking
            distance_threshold=1.2,  # Allow broader matches
            where=where_filter,
            min_score=min_score,
        )

        # Convert to AgentMatch objects
        matches: list[AgentMatch] = []
        for result in results:
            meta = result["metadata"]
            distance = result["distance"]

            # Calculate match score based on multiple factors
            score = self._calculate_match_score(result, criteria)

            # Determine match reasons
            reasons = self._get_match_reasons(result, criteria)

            # Create a minimal Agent for the match
            from agent_discovery.models import Agent, AgentType, Complexity

            agent = Agent(
                name=meta.get("agent_name", "unknown"),
                agent_type=AgentType(meta.get("agent_type", "agent")),
                description=meta.get("description", ""),
                category=Category(meta.get("category", "general")),
                tech_stack=meta.get("tech_stack", "").split(",") if meta.get("tech_stack") else [],
                languages=meta.get("languages", "").split(",") if meta.get("languages") else [],
                frameworks=meta.get("frameworks", "").split(",") if meta.get("frameworks") else [],
                subjects=meta.get("subjects", "").split(",") if meta.get("subjects") else [],
                complexity=Complexity(meta.get("complexity", "intermediate")),
                source_path=meta.get("source_path", ""),
                source_collection=meta.get("source_collection", ""),
            )

            matches.append(
                AgentMatch(
                    agent=agent,
                    score=score,
                    distance=distance,
                    match_reasons=reasons,
                )
            )

        # Sort by score (descending) and deduplicate
        matches.sort(key=lambda m: m.score, reverse=True)

        # Return top N unique matches with optional score/subject filtering
        seen: set[str] = set()
        unique: list[AgentMatch] = []
        subject_counts: dict[str, int] = {}

        for match in matches:
            if match.agent.name in seen:
                continue

            if min_score is not None and match.score < min_score:
                continue

            if subject_top_n:
                subjects = match.agent.subjects or [match.agent.category.value]
                applicable = [s for s in subjects if s in subject_top_n]
                if applicable:
                    # Skip if all applicable subjects are already at cap
                    if all(
                        subject_counts.get(subj, 0) >= subject_top_n[subj] for subj in applicable
                    ):
                        continue
                    # Increment the first subject still under cap
                    for subj in applicable:
                        if subject_counts.get(subj, 0) < subject_top_n[subj]:
                            subject_counts[subj] = subject_counts.get(subj, 0) + 1
                            break

            seen.add(match.agent.name)
            unique.append(match)

            if len(unique) >= n_results:
                break

        return unique

    def _build_filter(self, criteria: SearchCriteria) -> dict[str, Any] | None:
        """Build Chroma where filter from criteria.

        Args:
            criteria: Search criteria

        Returns:
            Chroma where filter or None
        """
        # Build OR filter for categories
        categories: list[str] = []
        for need in criteria.needs:
            cat = get_category_for_need(need)
            if cat:
                categories.append(cat.value)

        if not categories:
            return None

        if len(categories) == 1:
            return {"category": categories[0]}
        else:
            return {"$or": [{"category": c} for c in categories]}

    def _calculate_match_score(
        self,
        result: dict,
        criteria: SearchCriteria,
    ) -> float:
        """Calculate a match score for a result.

        Args:
            result: Search result from Chroma
            criteria: Search criteria

        Returns:
            Score between 0 and 1
        """
        base_score = result.get("score", 0.5)
        meta = result["metadata"]

        # Boost for language match
        if criteria.primary_language:
            languages = meta.get("languages", "").lower()
            if criteria.primary_language.lower() in languages:
                base_score += 0.1

        # Boost for framework match
        frameworks = meta.get("frameworks", "").lower()
        for fw in criteria.detected_frameworks:
            if fw.lower() in frameworks:
                base_score += 0.05

        # Boost for need/category match
        category = meta.get("category", "")
        for need in criteria.needs:
            cat = get_category_for_need(need)
            if cat and cat.value == category:
                base_score += 0.1
                break

        # Cap at 1.0
        return min(1.0, base_score)

    def _get_match_reasons(
        self,
        result: dict,
        criteria: SearchCriteria,
    ) -> list[str]:
        """Get reasons why this agent matched.

        Args:
            result: Search result
            criteria: Search criteria

        Returns:
            List of reason strings
        """
        reasons: list[str] = []
        meta = result["metadata"]

        # Check language match
        if criteria.primary_language:
            languages = meta.get("languages", "").lower()
            if criteria.primary_language.lower() in languages:
                reasons.append(f"Supports {criteria.primary_language}")

        # Check framework match
        frameworks = meta.get("frameworks", "").lower()
        for fw in criteria.detected_frameworks:
            if fw.lower() in frameworks:
                reasons.append(f"Works with {fw}")
                break

        # Check category/need match
        category = meta.get("category", "")
        category_names = {
            "testing": "Testing & QA",
            "security": "Security",
            "architecture": "Architecture",
            "devops": "DevOps",
            "database": "Database",
            "frontend": "Frontend",
            "backend": "Backend",
            "ai_ml": "AI/ML",
        }
        if category in category_names:
            reasons.append(f"Specializes in {category_names[category]}")

        # Add description as reason if we have few reasons
        if len(reasons) < 2 and meta.get("description"):
            reasons.append(meta["description"][:80])

        return reasons[:3]  # Limit to 3 reasons

    def quick_search(
        self,
        query: str,
        n_results: int = 5,
        min_score: float | None = None,
        subject_top_n: dict[str, int] | None = None,
    ) -> list[AgentMatch]:
        """Perform a quick semantic search without interactive questions.

        Args:
            query: Natural language search query
            n_results: Number of results

        Returns:
            List of AgentMatch objects
        """
        criteria = SearchCriteria(query_text=query)
        return self.discover(criteria, n_results, min_score=min_score, subject_top_n=subject_top_n)
