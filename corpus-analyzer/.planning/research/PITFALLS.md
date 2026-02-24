# Pitfalls Research

**Domain:** Adding tree-sitter TypeScript/JavaScript AST chunking to a Python 3.12 local search tool
**Researched:** 2026-02-24
**Confidence:** HIGH (official py-tree-sitter docs, GitHub issues, PyPI release notes, direct code inspection of existing chunker)

---

## Critical Pitfalls

### Pitfall 1: Grammar Package / Bindings Version Mismatch (ABI Incompatibility)

**What goes wrong:**
`tree-sitter` (the Python bindings) and `tree-sitter-typescript` (the grammar package) are versioned independently. If they are not pinned to a compatible pair, the runtime raises one of:
- `"Language's ABI is too new"` — grammar compiled against a newer tree-sitter core than the installed bindings
- `"Incompatible language version: N. Compatibility range M through M"` — grammar ABI version outside the range the runtime accepts
- `AttributeError: type object 'tree_sitter.Language' has no attribute 'build_library'` — bindings upgraded past 0.22.x but calling old API

This breaks silently in a different way from a Python import error: the parser object is created, then the parse call fails or returns a corrupt tree at runtime.

**Why it happens:**
`uv add tree-sitter` without a pinned version fetches the latest bindings. `uv add tree-sitter-typescript` fetches the latest grammar. These may have been released at different times with different ABI expectations. `tree-sitter-typescript` 0.23.x targets `tree-sitter` 0.23.x. `tree-sitter-typescript` 0.21.x targeted `tree-sitter` 0.21.x. Mixing them is not detected until runtime.

**How to avoid:**
Pin both packages to the same major.minor version in `pyproject.toml`:
```toml
[project]
dependencies = [
    "tree-sitter>=0.23.0,<0.24",
    "tree-sitter-typescript>=0.23.0,<0.24",
]
```
Write a smoke-test that runs at import time (or in the test suite) confirming the parser can successfully parse a two-line TypeScript snippet without error. This catches ABI mismatches on `uv sync`.

**Warning signs:**
- `uv run pytest` passes but `uv run corpus index` fails with an obscure C-level error or corrupt tree
- Installing `tree-sitter-typescript` after bumping `tree-sitter` without re-checking compatibility
- CI environment uses different package versions from dev because `uv.lock` was not committed

**Phase to address:** Phase 1 (dependency setup). The pinned versions and the smoke-test must be in the first commit, before any chunker code is written.

---

### Pitfall 2: Calling the Removed `Language.build_library()` or `Parser.set_language()` APIs

**What goes wrong:**
Code copied from tutorials, Stack Overflow answers, or the tree-sitter README prior to October 2023 calls APIs that were removed in py-tree-sitter 0.22.x and 0.23.x:

```python
# REMOVED in 0.22.x — raises AttributeError
Language.build_library("build/my-languages.so", ["vendor/tree-sitter-typescript"])

# REMOVED in 0.23.x — raises AttributeError
parser = Parser()
parser.set_language(Language(tsts.language_typescript(), "typescript"))
```

The current (0.23.x+) API is:
```python
import tree_sitter_typescript as tsts
from tree_sitter import Language, Parser

TS_LANGUAGE = Language(tsts.language_typescript())
TSX_LANGUAGE = Language(tsts.language_tsx())
parser = Parser(TS_LANGUAGE)   # language passed to constructor, not set_language()
```

**Why it happens:**
The py-tree-sitter API changed significantly three times between 0.20 and 0.23. Most web tutorials and Stack Overflow answers predate these changes. The official README on the `master` branch shows the current API, but cached/indexed copies still show the old patterns.

**How to avoid:**
Always verify against the official `py-tree-sitter` README at the exact PyPI version being used. Write the constructor call as `Parser(language_object)` — do not call `set_language()`. Do not call `Language.build_library()` — language capsules come pre-built from the `tree-sitter-typescript` PyPI package.

**Warning signs:**
- `AttributeError: type object 'tree_sitter.Language' has no attribute 'build_library'`
- `AttributeError: 'Parser' object has no attribute 'set_language'`
- Code has a `vendor/` or `build/` directory for grammar `.so` files

**Phase to address:** Phase 1 (dependency setup). Document the correct constructor patterns before writing any production code.

---

### Pitfall 3: Using a Single Grammar Object for Both `.ts` and `.tsx` Files

**What goes wrong:**
A developer loads one grammar and uses it for all four extensions (`.ts`, `.tsx`, `.js`, `.jsx`). JSX syntax (angle brackets used as element literals, JSX expressions, `<Component />`) is not valid TypeScript — it is only valid in TSX. Parsing a `.tsx` file with the TypeScript grammar produces an ERROR node at every JSX element. The chunker receives a "parsed" tree that is structurally invalid, extracts no named functions (because they are inside ERROR subtrees), and silently falls back to line-based chunking — which is exactly what the milestone is trying to replace.

The reverse also fails: parsing a `.ts` file that uses generic type parameters (`Array<string>`) with the TSX grammar may misparse the `<` as the start of a JSX element.

**Why it happens:**
The JavaScript ecosystem blurs the line between TypeScript and TSX (many editors handle both with one language server). But tree-sitter-typescript ships two distinct grammar objects because the grammars are genuinely incompatible:
```python
import tree_sitter_typescript as tsts
tsts.language_typescript()   # for .ts and .js files
tsts.language_tsx()          # for .tsx and .jsx files
```

**How to avoid:**
Dispatch on file extension in the chunker:
```python
_TS_EXTENSIONS = {".ts", ".js"}
_TSX_EXTENSIONS = {".tsx", ".jsx"}

def _get_ts_language(ext: str) -> Language:
    if ext in _TSX_EXTENSIONS:
        return TSX_LANGUAGE
    return TS_LANGUAGE
```
Add tests that explicitly parse a `.tsx` file containing JSX and verify the tree has no ERROR nodes at the root level.

**Warning signs:**
- All `.tsx` files fall through to line-based chunking despite having syntactically valid JSX
- `root_node.has_error` is True for `.tsx` files when parsed with `TS_LANGUAGE`
- Chunk type distribution shows `.tsx` files never producing `function_declaration` or `method_definition` chunk types

**Phase to address:** Phase 1 (chunker implementation). The extension dispatch table must be the first design decision.

---

### Pitfall 4: Missing Arrow Functions Because They Live Inside `lexical_declaration`

**What goes wrong:**
The chunker walks `root_node.children` looking for named node types: `function_declaration`, `class_declaration`, etc. It finds none in a TypeScript file that is entirely composed of:
```typescript
export const processItems = async (items: Item[]): Promise<void> => { ... };
export const formatName = (first: string, last: string): string => `${first} ${last}`;
```
These are `lexical_declaration` nodes, not `function_declaration` nodes. The function lives inside `variable_declarator > arrow_function`. The naïve chunker ignores these entirely and falls back to `chunk_lines()` — producing zero AST-aware chunks from a file that is 100% valid TypeScript functions.

**Why it happens:**
Python's `ast.parse()` gives you `ast.FunctionDef` for both `def foo():` and named assignments — but tree-sitter's TypeScript grammar is structurally faithful to the parse tree. `const foo = () => {}` is genuinely a `lexical_declaration` containing an `arrow_function`. The node type is NOT `function_declaration`.

**How to avoid:**
When building the list of top-level constructs to chunk, walk `lexical_declaration` nodes to check if their `variable_declarator` child has an `arrow_function` or `function_expression` value. If so, treat that `lexical_declaration` as a named function chunk. Useful node type check:
```python
def _is_named_arrow_function(node: Node) -> bool:
    """Return True if node is: const/let/var name = () => ..."""
    if node.type != "lexical_declaration":
        return False
    for child in node.children:
        if child.type == "variable_declarator":
            value = child.child_by_field_name("value")
            if value and value.type in ("arrow_function", "function_expression"):
                return True
    return False
```

**Warning signs:**
- A `.ts` test file consisting entirely of arrow functions produces zero AST chunks
- Chunk type distribution across the indexed agent library shows unexpectedly high line-based chunk ratios for `.ts` files
- `chunk_typescript()` returns `chunk_lines()` fallback for modern TypeScript that uses no `function_declaration` syntax

**Phase to address:** Phase 1 (chunker implementation). Include arrow function detection in the initial chunker spec.

---

### Pitfall 5: Off-By-One Line Numbers (tree-sitter is 0-indexed, the rest of the codebase is 1-indexed)

**What goes wrong:**
The existing `chunk_python()` function returns 1-indexed `start_line` and `end_line` values (matching the rest of the codebase, LanceDB schema, and chunk ID generation). The `chunk_typescript()` function uses `node.start_point[0]` and `node.end_point[0]` directly — but tree-sitter points are 0-indexed (row 0 = first line). The result: every chunk reports `start_line` that is one less than the actual line in the file. Chunk IDs are wrong; line-range display in search output is wrong.

**Why it happens:**
`node.start_point` returns `(row, column)` where `row` is 0-indexed. The Python `ast` module uses `node.lineno` which is 1-indexed. Mixing the two conventions without an explicit `+ 1` offset is the natural mistake.

**How to avoid:**
Always convert in one canonical place:
```python
start_line = node.start_point[0] + 1   # 0-indexed row → 1-indexed line
end_line   = node.end_point[0] + 1     # inclusive 1-indexed
```
Add a unit test asserting that `chunk_typescript()` on a file where the first function starts on line 1 reports `start_line == 1`, not `start_line == 0`.

**Warning signs:**
- `start_line: 0` appears in any chunk dict — the rest of the pipeline treats line 0 as invalid
- Line ranges in `corpus search` output are one line low for TS files but correct for Python files
- Chunk ID hash differs between two otherwise identical runs because the line number is wrong

**Phase to address:** Phase 1 (chunker implementation). Add the `+1` offset as an explicit named step in the test assertions, not as an implementation detail.

---

### Pitfall 6: `node.text` Returns `bytes`, Not `str` — and Is `None` Unless Source Was Passed as Bytes

**What goes wrong:**
`node.text` returns `bytes | None`. It is `None` if the parser was not given the source bytes directly (e.g., if a read callback was used). Calling `.decode("utf-8")` on `None` raises `AttributeError`. Passing `node.text` to a function expecting `str` silently constructs chunk text containing `b"..."` byte literals if the developer writes `str(node.text)` instead of `node.text.decode("utf-8")`.

**Why it happens:**
The existing `chunk_python()` function passes source as a string and then slices `lines[start_line - 1:end_line]`. The tree-sitter approach of using `source_bytes[node.start_byte:node.end_byte].decode("utf-8")` is a different pattern. Developers mixing the two approaches forget to decode.

**How to avoid:**
Pass source as `bytes` to the parser and use byte-range slicing consistently:
```python
source_bytes = path.read_bytes()
tree = parser.parse(source_bytes)
# ...
chunk_text = source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
```
Use `errors="replace"` rather than `errors="strict"` so malformed bytes in student or generated code do not crash the indexer. Wrap the entire parse attempt in `try/except Exception` and fall back to `chunk_lines()`.

**Warning signs:**
- `AttributeError: 'NoneType' object has no attribute 'decode'` in chunker
- Chunk text field contains Python bytes literal `b'...'` in the LanceDB store
- Non-ASCII identifiers (e.g., emoji in variable names, Unicode in comments) cause `UnicodeDecodeError`

**Phase to address:** Phase 1 (chunker implementation). Write a test with a file containing non-ASCII content as part of the first batch.

---

### Pitfall 7: `root_node.has_error` Is `True` But the Useful Nodes Are Still There

**What goes wrong:**
The developer checks `tree.root_node.has_error` and immediately falls back to `chunk_lines()` when it is `True`. However, tree-sitter's error recovery inserts ERROR nodes locally and continues parsing the rest of the file. A TypeScript file with one syntax error in one function still has valid parse trees for all other functions. Triggering a full fallback on any error discards correct AST structure for 95% of the file.

A second mistake: `has_error` is `True` on files with recoverable errors (e.g., a missing semicolon) that tree-sitter handles gracefully without producing invalid chunk boundaries.

**Why it happens:**
Developers treat `has_error` as a boolean "parse succeeded/failed" flag. It is not — it means "at least one ERROR or MISSING node exists somewhere in the tree." The tree is still structurally meaningful outside those nodes.

**How to avoid:**
Only fall back to `chunk_lines()` when the root node itself is an ERROR node (catastrophic failure to parse), or when the tree yields zero named top-level constructs after applying the node-type filter. Do not fall back merely because `has_error` is `True`.
```python
if tree.root_node.type == "ERROR":
    return chunk_lines(path)     # total parse failure
# otherwise: walk children, collect named constructs
# if the result list is empty, THEN fall back
if not constructs:
    return chunk_lines(path)
```

**Warning signs:**
- Files with a single TypeScript error (e.g., `const x = ;`) cause the entire file to fall back to line-based chunking
- `chunk_typescript()` never produces AST chunks on real-world code because many files have minor errors that set `has_error`

**Phase to address:** Phase 1 (chunker implementation). Add a test where the source has a deliberate ERROR node mid-file and assert that other functions in the file are still chunked by AST.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Unpin `tree-sitter` / `tree-sitter-typescript` versions | One less version decision upfront | ABI mismatch on next `uv sync` breaks CI silently | Never — pin both on day one |
| Use `chunk_lines()` fallback for all TS/JS until "later" | Defers complexity | The milestone goal is AST chunking — line-based is the status quo being replaced | Never — fallback is for parse failures only |
| Check only `function_declaration` node type, skip arrow functions | Simpler first pass | Misses 60–80% of modern TypeScript code that uses arrow functions | Acceptable in a first spike only, never in the shipped chunker |
| Use `node.text` without `.decode()` | Saves one call | Silent bytes-literal corruption in LanceDB; non-ASCII crashes | Never |
| Full file fallback on `has_error` | Simplest error handling | Most real-world TS files have minor errors; AST chunking degrades to useless | Never — use construct-level fallback only |
| Skip test for `.tsx` JSX files | Fewer test cases to write | JSX silently falls through to line-based chunking | Never — JSX is a primary use case |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `chunk_file()` dispatch | Adding `tree-sitter` import at module level — slow cold start | Import `tree_sitter` lazily inside `chunk_typescript()` or initialise parser once at module level using `try/except ImportError` with a clear error message |
| `chunk_file()` dispatch | Forgetting `.jsx` extension in the dispatch table | Map `{".ts", ".js", ".tsx", ".jsx"}` explicitly; `.jsx` must use `TSX_LANGUAGE`, not `TS_LANGUAGE` |
| Indexer `indexer.py` | Not guarding against `ImportError` if `tree-sitter` is absent | Wrap import in `try/except ImportError`; if absent, log a warning and proceed with `chunk_lines()` fallback for all TS/JS |
| LanceDB schema | Chunk type field stores raw node type strings from tree-sitter | Map grammar node types to the application's vocabulary (`function_declaration` → `"function"`, `class_declaration` → `"class"`) before storing |
| Test fixture files | Writing `.ts` test fixtures that only use `function_declaration` | Include fixtures that use: arrow functions in `const`, `interface_declaration`, `type_alias_declaration`, `class` with methods, and mixed files with JSX |
| `mypy --strict` | `node.text` typed as `bytes \| None` requires explicit None guard | Always assert or check `is not None` before `.decode()` — mypy will enforce this under `--strict` |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Constructing `Parser` and `Language` per file | 20–50ms overhead per file on initial index | Construct the parser once at module level; reuse across all calls to `chunk_typescript()` | Noticeable at >50 files; at 1k TS files it adds ~30s to `corpus index` |
| Parsing large generated files (e.g., bundled JS) | 2–5 second parse for a 20k-line minified file | Apply a character-count guard: skip AST parsing for files over ~50k chars; use `chunk_lines()` directly | Any minified bundle file in the index |
| Walking entire tree recursively in Python | Slow for deeply nested files | Use `node.children` iteration at the top level only; do not implement a full recursive tree walk in Python — only descend into `lexical_declaration` children | Files with 100+ top-level nodes |

---

## "Looks Done But Isn't" Checklist

- [ ] **`.jsx` extension dispatch:** `chunk_file()` routes `.jsx` to `chunk_typescript()` with `TSX_LANGUAGE` — not to `chunk_lines()` and not to `TS_LANGUAGE`
- [ ] **Arrow function detection:** `chunk_typescript()` produces AST chunks for files where all functions are defined as `const foo = () => {}`
- [ ] **1-indexed line numbers:** `start_line` in every chunk dict is `node.start_point[0] + 1`, not `node.start_point[0]`
- [ ] **`has_error` handling:** A file with one syntax error mid-file still produces AST chunks for all other functions (no full-file fallback triggered)
- [ ] **TSX JSX parse succeeds:** A `.tsx` file with `<Component />` syntax produces a tree with `root_node.has_error == False` (using `TSX_LANGUAGE`, not `TS_LANGUAGE`)
- [ ] **Non-ASCII content:** Files with Unicode in identifiers or comments do not crash the chunker (use `errors="replace"` on decode)
- [ ] **Grammar version pinned:** `pyproject.toml` pins `tree-sitter` and `tree-sitter-typescript` to the same major.minor; `uv.lock` is committed
- [ ] **`ImportError` guard:** If `tree-sitter` is not installed, `chunk_file()` falls back to `chunk_lines()` for TS/JS rather than raising `ImportError` at import time
- [ ] **Parser constructed once:** `TS_LANGUAGE`, `TSX_LANGUAGE`, and `Parser` instances are module-level constants, not created per call
- [ ] **mypy clean:** `uv run mypy src/` exits 0 with all `node.text` accesses guarded
- [ ] **Ruff clean:** `uv run ruff check .` exits 0
- [ ] **Tests green:** All 293 existing tests pass; new tests added for TS/TSX/JS/JSX chunking at parity with `test_chunk_python` coverage

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| ABI version mismatch breaks CI | LOW | Pin both packages to the same minor in `pyproject.toml`; `uv sync` |
| Old `set_language()` / `build_library()` API called | LOW | Replace with `Parser(Language(tsts.language_typescript()))` pattern |
| `.tsx` silently line-chunked due to wrong grammar | LOW | Add `_TSX_EXTENSIONS` dispatch; re-index affected files |
| Arrow functions produce no chunks | MEDIUM | Extend node-type walk to include `lexical_declaration` containing `arrow_function`; re-index all TS files |
| Off-by-one line numbers in stored chunks | MEDIUM | Add `+ 1` correction; re-index all TS/JS files (chunk IDs regenerated from content hash, so existing chunks get replaced cleanly) |
| Bytes not decoded (`node.text` corruption) | MEDIUM | Switch to `source_bytes[start_byte:end_byte].decode("utf-8", errors="replace")`; re-index |
| Full-file fallback on `has_error` eliminates AST chunking | MEDIUM | Change fallback condition to zero-named-constructs; re-index |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| ABI version mismatch | Phase 1: dependency setup | Smoke test: `from tree_sitter import Parser` + parse a 2-line TS snippet without error |
| Old API (`set_language`, `build_library`) | Phase 1: dependency setup | Code review: grep for `build_library` and `set_language` must return zero hits |
| Wrong grammar for `.tsx` / `.jsx` | Phase 1: chunker implementation | Test: parse `.tsx` file with JSX; assert `root_node.has_error == False` |
| Missing arrow function detection | Phase 1: chunker implementation | Test: file with only `const foo = () => {}` produces at least 1 AST chunk |
| Off-by-one line numbers | Phase 1: chunker implementation | Test: first function at line 1 produces `start_line == 1` |
| `node.text` bytes / None not decoded | Phase 1: chunker implementation | Test: file with non-ASCII identifier produces `str` chunk text without exception |
| `has_error` full-file fallback | Phase 1: chunker implementation | Test: file with one mid-file syntax error still produces AST chunks for valid functions |
| Parser constructed per file (perf) | Phase 2: integration + indexer wiring | Benchmark: indexing 200 TS files completes in under 10s |
| Large generated file parse timeout | Phase 2: integration + indexer wiring | Test: 50k-char minified JS returns `chunk_lines()` result, not a multi-second parse |
| `ImportError` not guarded in dispatch | Phase 2: integration + indexer wiring | Test: remove `tree-sitter` from env; `chunk_file()` still returns line chunks without exception |

---

## Sources

- py-tree-sitter official README (current `master`, 0.25.x API): https://github.com/tree-sitter/py-tree-sitter/blob/master/README.md
- py-tree-sitter releases page (API change history): https://github.com/tree-sitter/py-tree-sitter/releases
- tree-sitter-typescript PyPI (package structure, two language functions): https://pypi.org/project/tree-sitter-typescript/
- tree-sitter-typescript GitHub (node-types.json, grammar): https://github.com/tree-sitter/tree-sitter-typescript
- tree-sitter-typescript TypeScript node-types.json: https://github.com/tree-sitter/tree-sitter-typescript/blob/master/typescript/src/node-types.json
- py-tree-sitter discussion on TypeScript/TSX parser setup: https://github.com/tree-sitter/py-tree-sitter/discussions/231
- `Language.build_library` removal issue: https://github.com/tree-sitter/tree-sitter/issues/3499
- Tree-sitter packaging fragmentation article: https://ayats.org/blog/tree-sitter-packaging
- Direct code inspection: `src/corpus_analyzer/ingest/chunker.py` — existing `chunk_python()` and `chunk_file()` patterns

---
*Pitfalls research for: v1.5 TypeScript/JavaScript AST-aware chunking using tree-sitter*
*Researched: 2026-02-24*
