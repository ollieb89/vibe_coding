# Stack Research

**Domain:** corpus-analyzer v3 Intelligent Search — new capabilities only
**Researched:** 2026-02-24
**Confidence:** HIGH

---

## Context: What Already Exists (Do Not Re-add)

The following are confirmed in the active codebase. Do not research or re-add these.

| Already Present | Confirmed Version | Notes |
|-----------------|-------------------|-------|
| numpy | 2.4.2 (env-confirmed) | Transitive dep via lancedb + pandas; available to all modules |
| pandas | 3.0.1 (env-confirmed) | Direct dep |
| pyarrow | 23.0.1 (env-confirmed) | Transitive dep via lancedb |
| LanceDB | >=0.29.2 | Hybrid BM25+vector+RRF search already working |
| SQLite (stdlib) | — | graph.sqlite adjacency store exists |
| pathlib (stdlib) | — | File path manipulation throughout |
| fnmatch (stdlib) | — | Part of Python 3.12 stdlib |
| tree-sitter | >=0.25.0 | AST chunking for .py, .ts, .tsx, .js, .jsx |
| tree-sitter-language-pack | >=0.13.0 | TS/TSX/JS/JSX grammars |

numpy is confirmed available — no new install needed for any math in v3.

---

## Recommended Stack Additions

### New External Dependencies (2 packages total)

| Library | Version to Add | Purpose | Why Recommended |
|---------|----------------|---------|-----------------|
| `sentence-transformers` | `>=5.2.3` | Cross-encoder two-stage re-ranking (`--rerank` flag) | Official sbert.net library; `CrossEncoder` class loads MS-MARCO models locally; `rank()` method re-ranks passages with zero network calls at inference; v5.2.3 released 2026-02-17 |
| `networkx` | `>=3.6.1` | Graph centrality computation (indegree, PageRank) for `corpus index` | Pure-Python, zero required deps, 2.1 MB wheel; one-liner `nx.pagerank()` and `nx.in_degree_centrality()`; handles edge cases (dangling nodes, sinks); v3.6.1 released 2025-12-08 |

### Zero New Dependencies (Use What Exists)

| v3 Feature | Implementation | Why No New Dep |
|------------|----------------|----------------|
| MMR diversity re-ranking (RANK-01) | Pure numpy (already in env) | Cosine sim = `np.dot(a,b)/(norm(a)*norm(b))`; full MMR loop is ~20 lines of numpy broadcasting; scikit-learn's `cosine_similarity` is identical math |
| `--exclude-path <glob>` (MULTI-02) | `fnmatch.fnmatch()` from stdlib | Handles `*`, `**`, `?`, `[ranges]`; verified correct for all expected patterns in environment |
| Multiple `--query` AND-intersection (MULTI-01) | Existing LanceDB search + Python set intersection | Run each query independently, intersect result IDs in-process; no library needed |
| Contiguous sub-chunk merging (RANK-02) | Plain Python list grouping | Sort chunks by path + start_line, merge adjacent same-file chunks; ~10 lines |
| `--within-graph` component filter (GSCOPE-01) | networkx `nx.weakly_connected_components()` | networkx already added for centrality; no additional library |

---

## Library Detail: MMR (Maximal Marginal Relevance)

**Verdict: No new dependency. Implement with numpy only.**

**Confidence: HIGH** — MMR is standard algorithm; numpy 2.4.2 confirmed in environment; verified no sklearn needed.

MMR re-ranks an initial result set iteratively. At each step, it selects the candidate that maximises relevance to the query while minimising redundancy with already-selected results:

```
mmr_score(d) = λ * sim(d, query) - (1 - λ) * max(sim(d, s) for s in selected)
```

The cosine similarity computation requires only numpy, which is already in the environment:

```python
import numpy as np

def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two 1-D vectors."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))
```

For batch computation against a matrix of selected embeddings, numpy broadcasting handles it in one line — no sklearn `cosine_similarity` needed.

**Why not sklearn:** scikit-learn is a 12+ MB dependency added solely for a function expressible as `np.dot / np.linalg.norm`. The project already has numpy; sklearn would be pure overhead.

**Integration point:** A new `search/mmr.py` module. Called inside `CorpusSearch.search()` after initial LanceDB retrieval, before returning results. LanceDB result objects carry `vector` fields that can be used directly. Lambda parameter defaults to 0.7 (prefer relevance over diversity; tunable).

---

## Library Detail: Cross-Encoder Reranking

**Verdict: Add `sentence-transformers>=5.2.3` as optional extra.**

**Confidence: HIGH** — v5.2.3 confirmed on PyPI (2026-02-17); API confirmed from official sbert.net docs; model sizes verified from HuggingFace Hub.

The `sentence_transformers.CrossEncoder` class loads BERT-based reranker models from HuggingFace and runs entirely locally with no network calls at inference time. This satisfies the offline-first constraint.

**Recommended model:** `cross-encoder/ms-marco-MiniLM-L6-v2`

| Property | Value |
|----------|-------|
| Model weights (safetensors) | ~91 MB |
| Throughput on CPU | ~1800 passages/sec |
| NDCG@10 (TREC Deep Learning 2019) | 74.30 |
| MRR@10 (MS MARCO Passage Reranking) | 39.01 |
| Download location | HuggingFace Hub (one-time; cached to `~/.cache/huggingface/`) |

The model download is a one-time operation on first use of `--rerank`. After that, inference is fully offline. This mirrors how the Ollama embedding model works (one-time pull, local inference).

**Alternative model:** `cross-encoder/ms-marco-TinyBERT-L2-v2` (~14 MB, 9000 docs/sec, NDCG@10 69.84). Suitable for users on low-spec hardware. Consider exposing via a `--rerank-model` option defaulting to MiniLM-L6.

**API (sentence-transformers v5.x):**

```python
from sentence_transformers import CrossEncoder

# Load once (cached after first run)
model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")

# rank() returns list of {"corpus_id": int, "score": float, "text": str}
reranked = model.rank(query, [r.text for r in top20], return_documents=True)
```

**Integration point:** Lazy-imported inside the `--rerank` code path only — do not import at module top level. This ensures users without sentence-transformers installed see no startup impact or error.

**Optional extra pattern in pyproject.toml:**

```toml
[project.optional-dependencies]
rerank = ["sentence-transformers>=5.2.3"]
```

Install: `uv sync --extra rerank` for users who want `--rerank`.

**mypy note:** Add `[[tool.mypy.overrides]] module = ["sentence_transformers"] ignore_missing_imports = true` — stubs are incomplete in the current package.

**Error handling:** If `--rerank` is used but sentence-transformers is not installed, raise a clear `ImportError` with install instructions: `uv add sentence-transformers`. Do not fail at startup.

---

## Library Detail: Graph Centrality

**Verdict: Add `networkx>=3.6.1` as core dependency.**

**Confidence: HIGH** — v3.6.1 confirmed on PyPI (2025-12-08); API stable across 3.x series; in_degree_centrality and pagerank API confirmed from official docs.

The corpus graph store (`graph.sqlite`) already contains a directed adjacency table (`source_path`, `target_path`). Computing indegree centrality and PageRank requires loading those rows into a graph structure and running standard algorithms.

**Why networkx over roll-your-own:**
- `nx.in_degree_centrality(G)` — one line; returns normalised indegree per node
- `nx.pagerank(G, alpha=0.85)` — one line; handles dangling nodes, sink nodes, convergence
- Roll-your-own PageRank power iteration is ~50 lines of numpy; networkx is battle-tested
- 2.1 MB wheel; zero required dependencies (pure Python); does not add numpy requirement (already present)

**Why core dep (not optional):** Centrality computation runs during `corpus index`, not only on demand. It is not user-facing like `--rerank`, so there is no flag to gate it behind.

**Why not scipy sparse PageRank:**
- scipy is ~35 MB for a problem with <10K nodes (typical corpus graph)
- networkx PageRank is fast enough for any expected corpus size; convergence at <10K nodes is near-instant

**Integration point:** `graph/centrality.py` module.

```python
import networkx as nx

def compute_centrality(adjacency_rows: list[tuple[str, str]]) -> dict[str, float]:
    G = nx.DiGraph()
    G.add_edges_from(adjacency_rows)
    # Use PageRank as primary score (subsumes indegree signal)
    return nx.pagerank(G, alpha=0.85)
```

Centrality scores stored back to SQLite (new `centrality` column or table). Queried during search to apply score multiplier to high-centrality files (GCENT-01).

**mypy note:** Add `[[tool.mypy.overrides]] module = ["networkx"] ignore_missing_imports = true` — networkx ships stubs but they are incomplete for some functions.

---

## Library Detail: Glob Path Filtering

**Verdict: No new dependency. Use stdlib `fnmatch.fnmatch()`.**

**Confidence: HIGH** — verified in project environment against all expected pattern types.

The `--exclude-path <glob>` requirement (MULTI-02) needs to match user patterns against file path strings. Environment testing confirms stdlib `fnmatch.fnmatch` handles all expected cases:

```
Pattern              Path                          Result
'**/tests/**'     -> 'src/foo/tests/bar.md'     -> True
'**/*.py'         -> 'src/foo/bar.py'            -> True
'dist/**'         -> 'dist/build/out.js'         -> True
'*.md'            -> 'README.md'                 -> True
```

**Why not `pathlib.PurePosixPath.match()`:** pathlib's `match()` is right-anchored; prefix-only patterns like `dist/**` return False. `fnmatch.fnmatch` does not have this limitation and handles all expected patterns correctly.

**Why not wcmatch or pathspec:** These libraries provide .gitignore-style extended glob matching, which is overkill for a simple `--exclude-path` flag. stdlib fnmatch covers the documented patterns.

**Usage:**

```python
import fnmatch

def path_matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, p) for p in patterns)
```

---

## Installation

```bash
# Add new core dependency
uv add "networkx>=3.6.1"

# Add optional reranking extra
uv add --optional rerank "sentence-transformers>=5.2.3"
```

After adding, pyproject.toml should contain:

```toml
[project.dependencies]
# ... existing ...
networkx = ">=3.6.1"

[project.optional-dependencies]
rerank = ["sentence-transformers>=5.2.3"]
dev = ["pytest>=8.0.0", "pytest-cov>=4.1.0", "ruff>=0.4.0", "mypy>=1.9.0"]
```

Users who want `--rerank`: `uv sync --extra rerank`
Users without it: zero overhead, no torch/transformers import at startup

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| numpy MMR (no new dep) | scikit-learn `cosine_similarity` | scikit-learn adds 12 MB; `np.dot / np.linalg.norm` is identical math; numpy already present |
| networkx 3.6.1 | scipy sparse PageRank | scipy is ~35 MB; corpus graphs are <10K nodes; networkx is simpler and sufficient |
| networkx 3.6.1 | Roll-your-own power iteration | ~50 lines vs one-liner; networkx handles dangling nodes and convergence edge cases |
| sentence-transformers 5.x | Ollama LLM re-ranking | LLM re-ranking needs a prompt round-trip (~200–500ms per result batch); cross-encoder is ~0.5ms/pair; deterministic; no model warm-up needed |
| sentence-transformers 5.x | Cohere / OpenAI / Jina rerank APIs | Cloud dependency; violates offline-first constraint |
| sentence-transformers as optional extra | sentence-transformers as core dep | Pulls torch (~800 MB) for all users; most users will not use `--rerank`; optional extra keeps install lean |
| fnmatch stdlib | wcmatch library | Overkill; stdlib handles all v3 exclusion patterns |
| fnmatch stdlib | pathspec library | pathspec is .gitignore-syntax; fnmatch glob syntax is simpler and sufficient |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| scikit-learn | 12 MB for one function already expressible in 2 lines of numpy | `np.dot(a,b) / (np.linalg.norm(a) * np.linalg.norm(b))` |
| faiss | GPU-accelerated ANN index; overkill for MMR on top-20 candidates post-retrieval | numpy matrix multiply |
| scipy | 35 MB; no current v3 feature requires it | networkx for graph math; numpy for array math |
| rank-bm25 | Duplicates LanceDB's built-in BM25/tantivy | LanceDB already handles BM25 |
| Cohere / Jina / OpenAI rerank API clients | Cloud dependency; violates offline-first constraint | sentence-transformers CrossEncoder |
| pathspec | .gitignore-style patterns; overkill for single `--exclude-path` flag | stdlib fnmatch |
| wcmatch | Overkill for glob exclusion | stdlib fnmatch |

---

## Version Compatibility

| Package | Version | Python | Notes |
|---------|---------|--------|-------|
| `sentence-transformers` | 5.2.3 | 3.12 | Requires torch (transitive); no numpy 2.x compat issues in 5.x |
| `networkx` | 3.6.1 | >=3.11 | Pure Python; no C extensions; confirmed Python 3.12 compatible |
| `networkx` + numpy | any | — | networkx uses numpy optionally for sparse ops; not required |
| mypy strict + sentence-transformers | — | — | Add `ignore_missing_imports = true` override |
| mypy strict + networkx | — | — | Add `ignore_missing_imports = true` override |

---

## Stack Patterns by Variant

**If `--rerank` flag is not invoked:**
- sentence-transformers is NOT imported (lazy import inside flag branch)
- torch is not loaded at startup; no overhead for users without --extra rerank installed
- No HuggingFace model download occurs

**If corpus graph is empty (no edges in graph.sqlite):**
- `nx.DiGraph()` with no edges returns empty dicts for in_degree and pagerank
- Centrality scores default to 0.0; score multiplier is 1.0 (neutral); search unaffected

**If user has no internet (after first `--rerank` use):**
- HuggingFace model is cached to `~/.cache/huggingface/hub/`; fully offline after first download
- Same pattern as Ollama: one-time pull, local inference thereafter

**If `--exclude-path` receives multiple patterns:**
- Call `path_matches_any(path, patterns)` with a list; `any()` short-circuits

---

## Sources

- [PyPI sentence-transformers](https://pypi.org/project/sentence-transformers/) — version 5.2.3, released 2026-02-17 (HIGH — direct PyPI fetch)
- [sbert.net Cross-Encoder Pretrained Models](https://sbert.net/docs/cross_encoder/pretrained_models.html) — model table, NDCG@10 74.30 for MiniLM-L6-v2, throughput 1800 docs/sec (HIGH — official docs, fetched 2026-02-24)
- [sbert.net Cross-Encoder Usage](https://sbert.net/docs/cross_encoder/usage/usage.html) — `CrossEncoder`, `predict()`, `rank()` API signature (HIGH — official docs)
- [HuggingFace cross-encoder/ms-marco-MiniLM-L6-v2](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2) — safetensors model weight ~91 MB (MEDIUM — HuggingFace Hub page)
- [PyPI networkx](https://pypi.org/project/networkx/) — version 3.6.1, released 2025-12-08, 2.1 MB wheel, zero required deps (HIGH — direct PyPI fetch)
- [NetworkX Centrality Docs](https://networkx.org/documentation/stable/reference/algorithms/centrality.html) — `in_degree_centrality()` API (HIGH — official docs)
- [NetworkX PageRank Docs](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.link_analysis.pagerank_alg.pagerank.html) — `pagerank(G, alpha=0.85)` signature (HIGH — official docs)
- [Python stdlib fnmatch](https://docs.python.org/3/library/fnmatch.html) — `fnmatch.fnmatch()` pattern matching semantics (HIGH — official docs; verified in environment)
- numpy cosine similarity — standard linear algebra; verified correct in Python 3.12 / numpy 2.4.2 environment via `uv run python` (HIGH — env-verified)
- Environment verification — `uv run python -c "import numpy; print(numpy.__version__)"` → 2.4.2; fnmatch pattern tests run against all expected glob forms (HIGH — direct env test)

---

*Stack research for: corpus-analyzer v3 Intelligent Search additions*
*Researched: 2026-02-24*
