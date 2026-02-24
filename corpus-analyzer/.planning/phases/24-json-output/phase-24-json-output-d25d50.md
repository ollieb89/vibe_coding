# Phase 24 JSON Output Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `corpus search` results can be piped to other tools via a machine-readable JSON format, fully suppressing Rich formatting when `--output json` is used.

**Architecture:** Add an `--output` flag (default `"text"`) to the CLI's `search` command. When set to `"json"`, the command collects all results into a list of dictionaries, mapping internal LanceDB keys (like `_relevance_score` and `file_path`) to the required API vocabulary (`score`, `path`, etc.), and uses standard `print(json.dumps(...))` to emit them to stdout. Warnings about "No results" are replaced with an empty JSON array `[]` to maintain parseability.

**Tech Stack:** Python, Typer, `json`

---

### Task 1: Basic JSON Output Support

**Files:**
- Create: `tests/cli/test_search_json.py`
- Modify: `src/corpus_analyzer/cli.py`

**Step 1: Write the failing test**

```python
import json
from typer.testing import CliRunner
from corpus_analyzer.cli import app

runner = CliRunner()

def test_search_json_output():
    # Use a query that should return results (assuming index is populated, or mock if needed)
    # Note: Using the name filter or a generic query to get at least one item.
    result = runner.invoke(app, ["search", "test", "--output", "json"])
    
    # Will fail until implemented
    assert result.exit_code == 0
    
    # Must be valid JSON
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    
    if len(data) > 0:
        first = data[0]
        assert "path" in first
        assert "score" in first
        assert "construct_type" in first
        assert "chunk_name" in first
        assert "start_line" in first
        assert "end_line" in first
        assert "text" in first
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/cli/test_search_json.py -v`
Expected: FAIL because `--output` flag doesn't exist yet.

**Step 3: Write minimal implementation**

In `src/corpus_analyzer/cli.py`, add `import json`.
Modify `search_command` to accept `output: Annotated[str, typer.Option("--output", "-o", help="Output format: text or json")] = "text",`.

At the end of `search_command`, before `if not results:`:
```python
    if output == "json":
        json_results = []
        for r in results:
            json_results.append({
                "path": r.get("file_path", ""),
                "score": r.get("_relevance_score", 0.0),
                "construct_type": r.get("construct_type"),
                "chunk_name": r.get("chunk_name"),
                "start_line": r.get("start_line", 0),
                "end_line": r.get("end_line", 0),
                "text": r.get("chunk_text", ""),
            })
        print(json.dumps(json_results, indent=2))
        return
        
    # Existing text-based output logic follows...
    if not results:
        if min_score > 0.0:
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/cli/test_search_json.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/cli/test_search_json.py src/corpus_analyzer/cli.py
git commit -m "feat(cli): add --output json flag to corpus search"
```

### Task 2: Ensure warnings are suppressed and edge cases handled

**Files:**
- Modify: `tests/cli/test_search_json.py`
- Modify: `src/corpus_analyzer/cli.py`

**Step 1: Write the failing test for empty results**

```python
def test_search_json_empty_results():
    result = runner.invoke(app, ["search", "this-will-definitely-not-match-anything-12345", "--output", "json"])
    
    assert result.exit_code == 0
    # Should output exactly "[]" with no warnings
    assert result.stdout.strip() == "[]"
    data = json.loads(result.stdout)
    assert data == []
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/cli/test_search_json.py::test_search_json_empty_results -v`
Expected: Might output Rich warnings (e.g. `No results for...`) instead of `[]` if not properly suppressed.

**Step 3: Write minimal implementation**

Ensure that in `src/corpus_analyzer/cli.py`, `if output == "json":` occurs *before* any text warnings (like the `if not results:` check that prints yellow warnings, and the `if construct and sort == "construct"` note).

The structure in `search_command` should be:
```python
    try:
        results = search.hybrid_search(...)
    except ValueError as e: ...

    if output == "json":
        json_results = [...]
        print(json.dumps(json_results, indent=2))
        return

    # Text output warnings and formatting follows...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/cli/test_search_json.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/cli/test_search_json.py src/corpus_analyzer/cli.py
git commit -m "test(cli): verify empty json array on no results"
```
