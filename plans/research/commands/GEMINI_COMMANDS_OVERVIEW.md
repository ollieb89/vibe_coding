# Gemini CLI Custom Commands & Workflows Overview

## 1. Executive Summary
The "Gemini CLI" ecosystem centers around the official `google-gemini/gemini-cli` tool, which supports robust customization via **TOML-based** command definitions. Unlike Claude Code's Markdown approach, Gemini CLI uses structured configuration files to define prompts, arguments, and shell execution.

**Key Insight:** The power of Gemini CLI lies in its **Headless Mode** for CI/CD (GitHub Actions) and its **Project-Scoped Context** (`GEMINI.md`).

---

## 2. Top Repositories & Command Suites

| Repository | Focus | Best For |
| :--- | :--- | :--- |
| **`google-gemini/gemini-cli`** | Official Core | The definitive reference for `.toml` command syntax and headless mode. |
| **`Piebald-AI/awesome-gemini-cli`** | Curated Ecosystem | Finding extensions, prompts, and community-built command suites. |
| **`philschmid/gemini-cli-extension`** | Developer Productivity | Real-world examples of `.toml` commands for coding workflows. |
| **`google-github-actions/run-gemini-cli`** | CI/CD Automation | Integrating Gemini into GitHub workflows (PR reviews, triage). |

---

## 3. The Architecture of Custom Commands

### File Structure & Syntax
Gemini CLI uses **TOML** files located in specific directories:
*   **Global:** `~/.gemini/commands/my-command.toml`
*   **Project:** `.gemini/commands/my-command.toml`

**Example `.toml` Command:**
```toml
# .gemini/commands/review.toml
description = "Review the current staged changes"
[prompt]
text = """
Act as a senior engineer. Review the following staged changes for security and performance issues.
Diff:
!{git diff --staged}
"""
```

### Key Syntax Features
*   **`!{cmd}`**: Executes a shell command and injects the output (e.g., `!{git status}`).
*   **`{{args}}`**: Injects user arguments passed to the slash command (e.g., `/ticket 123` -> `{{args}}` is `123`).
*   **`@{file}`**: Injects file content.

---

## 4. Essential Command Recipes

### 🛡️ Automated Code Review (`/review`)
*   **Goal:** Instant feedback on staged changes.
*   **Configuration:**
    ```toml
    # review.toml
    description = "Review staged changes"
    text = "Review these changes:\n!{git diff --staged}"
    ```
*   **Workflow:** User stages files -> runs `/review` -> receives feedback before committing.

### 📝 Strategic Planning (`/plan`)
*   **Goal:** Break down complex tasks before implementation.
*   **Configuration:**
    ```toml
    # plan.toml
    description = "Create a step-by-step implementation plan"
    text = "Create a detailed checklist for implementing: {{args}}"
    ```
*   **Workflow:** `/plan "Add OAuth2 support"` -> Gemini generates a numbered list.

### 🤖 CI/CD Integration (Headless)
*   **Goal:** Automated PR reviews on GitHub.
*   **Mechanism:** Use `google-github-actions/run-gemini-cli`.
*   **Workflow:** GitHub Action triggers on PR -> runs `gemini-cli` in headless mode -> posts comment on PR.

### 🧠 Project Context (`GEMINI.md`)
Similar to `CLAUDE.md`, this file in the project root is automatically loaded to provide:
*   Project architecture overview.
*   Coding standards (e.g., "Use TypeScript", "No `any` types").
*   Common build/test commands.

---

## 5. Implementation Strategy

To align with the "Gemini CLI" ecosystem standards:

1.  **Initialize Context:** Create a `GEMINI.md` in the project root containing your architectural guidelines.
2.  **Create Command Directory:** `mkdir -p .gemini/commands/`
3.  **Implement Core TOMLs:**
    *   `review.toml`: For `git diff` analysis.
    *   `commit.toml`: For generating commit messages.
    *   `plan.toml`: For task breakdown.
4.  **Explore CI/CD:** If using GitHub, add the `run-gemini-cli` action to your `.github/workflows/`.

**References:**
*   [Gemini CLI Docs - Custom Commands](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/custom-commands.md)
*   [Awesome Gemini CLI](https://github.com/Piebald-AI/awesome-gemini-cli)
