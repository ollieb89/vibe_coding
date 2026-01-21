"""Question bank and generator for interactive agent discovery."""

from typing import Any

from agent_discovery.models import Category, CodebaseProfile, Question, SearchCriteria

# Question bank - defines all possible questions
QUESTION_BANK: list[dict[str, Any]] = [
    {
        "id": "project_type",
        "text": "What type of project are you building?",
        "question_type": "single",
        "options": [
            {"value": "frontend", "label": "Frontend Web App (React, Vue, etc.)"},
            {"value": "backend", "label": "Backend API (FastAPI, Express, etc.)"},
            {"value": "fullstack", "label": "Full-Stack Application"},
            {"value": "cli", "label": "CLI Tool / Script"},
            {"value": "library", "label": "Library / Package"},
            {"value": "mobile", "label": "Mobile App"},
            {"value": "devops", "label": "DevOps / Infrastructure"},
        ],
        "maps_to": ["category"],
    },
    {
        "id": "primary_language",
        "text": "What is your primary programming language?",
        "question_type": "single",
        "options": [
            {"value": "python", "label": "Python"},
            {"value": "typescript", "label": "TypeScript"},
            {"value": "javascript", "label": "JavaScript"},
            {"value": "java", "label": "Java / Kotlin"},
            {"value": "csharp", "label": "C# / .NET"},
            {"value": "go", "label": "Go"},
            {"value": "rust", "label": "Rust"},
            {"value": "ruby", "label": "Ruby"},
            {"value": "php", "label": "PHP"},
            {"value": "other", "label": "Other"},
        ],
        "maps_to": ["languages"],
    },
    {
        "id": "framework",
        "text": "What frameworks are you using?",
        "question_type": "multi",
        "options": [
            {"value": "nextjs", "label": "Next.js"},
            {"value": "react", "label": "React"},
            {"value": "vue", "label": "Vue.js"},
            {"value": "angular", "label": "Angular"},
            {"value": "fastapi", "label": "FastAPI"},
            {"value": "django", "label": "Django"},
            {"value": "flask", "label": "Flask"},
            {"value": "express", "label": "Express / Node.js"},
            {"value": "spring", "label": "Spring Boot"},
            {"value": "dotnet", "label": ".NET / ASP.NET"},
            {"value": "playwright", "label": "Playwright"},
            {"value": "none", "label": "None / Other"},
        ],
        "maps_to": ["frameworks", "tech_stack"],
    },
    {
        "id": "needs",
        "text": "What kind of help do you need? (select all that apply)",
        "question_type": "multi",
        "options": [
            {"value": "architecture", "label": "Architecture & System Design"},
            {"value": "testing", "label": "Testing & QA"},
            {"value": "security", "label": "Security Review"},
            {"value": "performance", "label": "Performance Optimization"},
            {"value": "debugging", "label": "Debugging & Troubleshooting"},
            {"value": "documentation", "label": "Documentation"},
            {"value": "devops", "label": "DevOps & CI/CD"},
            {"value": "database", "label": "Database Design"},
            {"value": "ai_ml", "label": "AI/ML Integration"},
            {"value": "planning", "label": "Planning & Requirements"},
        ],
        "maps_to": ["category"],
    },
    {
        "id": "experience_level",
        "text": "What is your experience level with this stack?",
        "question_type": "single",
        "options": [
            {"value": "beginner", "label": "Beginner - Learning the basics"},
            {"value": "intermediate", "label": "Intermediate - Can build features"},
            {"value": "advanced", "label": "Advanced - Deep expertise"},
        ],
        "maps_to": ["complexity"],
    },
    {
        "id": "focus_query",
        "text": "Any specific areas you want to focus on? (free text)",
        "question_type": "text",
        "options": [],
        "maps_to": ["query_text"],
    },
]


class QuestionGenerator:
    """Generates relevant questions based on codebase analysis."""

    def __init__(self, question_bank: list[dict[str, Any]] | None = None):
        """Initialize question generator.

        Args:
            question_bank: Custom question bank (default uses QUESTION_BANK)
        """
        self.questions = question_bank or QUESTION_BANK

    def get_all_questions(self) -> list[Question]:
        """Get all questions from the bank.

        Returns:
            List of Question objects
        """
        return [Question(**q) for q in self.questions]

    def get_questions_for_profile(
        self,
        profile: CodebaseProfile,
    ) -> list[Question]:
        """Get relevant questions based on codebase profile.

        Skips questions that can be inferred from the profile.

        Args:
            profile: Analyzed codebase profile

        Returns:
            List of relevant Question objects
        """
        questions: list[Question] = []

        for q_data in self.questions:
            q = Question(**q_data)

            # Skip language question if already detected
            if q.id == "primary_language" and profile.languages:
                continue

            # Skip framework question if already detected
            if q.id == "framework" and profile.frameworks:
                continue

            questions.append(q)

        return questions

    def process_answers(
        self,
        answers: dict[str, Any],
        profile: CodebaseProfile | None = None,
    ) -> SearchCriteria:
        """Process user answers into search criteria.

        Args:
            answers: Dictionary of question_id -> answer
            profile: Optional codebase profile for context

        Returns:
            SearchCriteria object for querying
        """
        criteria = SearchCriteria()

        # Start with detected values from profile
        if profile:
            criteria.detected_languages = profile.languages
            criteria.detected_frameworks = profile.frameworks

        # Process answers
        for question_id, answer in answers.items():
            if question_id == "project_type":
                criteria.project_type = answer

            elif question_id == "primary_language":
                criteria.primary_language = answer

            elif question_id == "framework":
                if isinstance(answer, list):
                    criteria.detected_frameworks.extend(answer)
                else:
                    criteria.detected_frameworks.append(answer)

            elif question_id == "needs":
                if isinstance(answer, list):
                    criteria.needs = answer
                else:
                    criteria.needs = [answer]

            elif question_id == "experience_level":
                from agent_discovery.models import Complexity

                criteria.complexity_preference = Complexity(answer)

            elif question_id == "focus_query":
                criteria.query_text = str(answer) if answer else ""

        return criteria

    def build_search_query(self, criteria: SearchCriteria) -> str:
        """Build a natural language search query from criteria.

        Args:
            criteria: SearchCriteria object

        Returns:
            Natural language query string
        """
        parts: list[str] = []

        # Add project type context
        if criteria.project_type:
            type_names = {
                "frontend": "frontend web development",
                "backend": "backend API development",
                "fullstack": "full-stack application",
                "cli": "command-line tool",
                "library": "library development",
                "devops": "DevOps and infrastructure",
            }
            parts.append(type_names.get(criteria.project_type, criteria.project_type))

        # Add language context
        if criteria.primary_language:
            parts.append(criteria.primary_language)

        # Add frameworks
        if criteria.detected_frameworks:
            parts.extend(criteria.detected_frameworks[:3])

        # Add needs
        need_names = {
            "architecture": "architecture design",
            "testing": "testing and QA",
            "security": "security review",
            "performance": "performance optimization",
            "debugging": "debugging",
            "documentation": "documentation",
            "devops": "DevOps CI/CD",
            "database": "database design",
            "ai_ml": "AI/ML integration",
            "planning": "project planning",
        }
        for need in criteria.needs[:3]:
            parts.append(need_names.get(need, need))

        # Add free text query
        if criteria.query_text:
            parts.append(criteria.query_text)

        return " ".join(parts) if parts else "general purpose coding assistant"


# Mapping from needs to categories for filtering
NEEDS_TO_CATEGORY: dict[str, Category] = {
    "architecture": Category.ARCHITECTURE,
    "testing": Category.TESTING,
    "security": Category.SECURITY,
    "performance": Category.DEVOPS,
    "debugging": Category.QUALITY,
    "documentation": Category.DOCUMENTATION,
    "devops": Category.DEVOPS,
    "database": Category.DATABASE,
    "ai_ml": Category.AI_ML,
    "planning": Category.PLANNING,
}


def get_category_for_need(need: str) -> Category | None:
    """Map a need to a category.

    Args:
        need: Need value from answers

    Returns:
        Corresponding Category or None
    """
    return NEEDS_TO_CATEGORY.get(need)
