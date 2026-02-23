# Codebase Concerns

**Analysis Date:** 2026-02-23

## Tech Debt

**Duplicate Rewriter Implementations:**
- Issue: Two parallel rewriter implementations with overlapping functionality
- Files: `src/corpus_analyzer/llm/rewriter.py` (447 lines), `src/corpus_analyzer/llm/unified_rewriter.py` (453 lines)
- Impact: Code maintenance burden, inconsistent behavior, duplicated logic for quality scoring, template loading, and prompt building
- Fix approach: Consolidate into single unified rewriter. Verify `unified_rewriter.py` has all features from `rewriter.py`, deprecate old version, update CLI references

**Secondary Database Schema Fields Without Storage:**
- Issue: `ClassificationResult` includes `secondary_category` and `secondary_confidence` that are computed but not persisted to database
- Files: `src/corpus_analyzer/classifiers/document_type.py` (lines 269-277), `src/corpus_analyzer/core/database.py` (lines 161-176)
- Impact: Secondary category insights are lost when documents are reloaded from database; potential improvement data loss
- Fix approach: Add `secondary_category` and `secondary_confidence` columns to documents table, update serialization in `_doc_to_dict()` and `_row_to_document()`

**Unclosed Code Block Handling in Chunked Processor:**
- Issue: In `split_on_headings()`, unclosed code blocks treated as code atoms but behavior undefined
- Files: `src/corpus_analyzer/llm/chunked_processor.py` (line 126)
- Impact: If document ends with unclosed code fence, chunk structure may be incorrect; comment indicates unresolved design decision
- Fix approach: Explicitly handle EOF with unclosed code block: either (1) close the block programmatically, (2) raise error, or (3) document expected behavior

## Known Bugs

**Placeholder Pattern Regex Side Effects:**
- Issue: `PLACEHOLDER_PATTERN = re.compile(r'\$[A-Z_]+')` in both rewriter files could match valid identifiers in code blocks
- Files: `src/corpus_analyzer/llm/rewriter.py` (line 15), `src/corpus_analyzer/llm/unified_rewriter.py` (line 22)
- Trigger: Document containing code with variable names like `$CONFIG_VAR` or `$USER_ID` in shell/bash blocks
- Workaround: None currently; code gets replaced with `[user-defined]`
- Fix approach: Apply replacement only outside code blocks, or use more specific pattern to target template placeholders

**IDF Calculation Bug in TF-IDF Similarity:**
- Issue: IDF calculation in `compute_tfidf_similarity()` is incorrect
- Files: `src/corpus_analyzer/classifiers/document_type.py` (line 116)
- Problem: `idf = math.log(len(category_patterns) / sum(1 for p in category_patterns.values() if token in ' '.join(p)))` divides by count of patterns containing token, not document frequency; should be inverted
- Impact: TF-IDF similarity scores biased incorrectly; classification confidence potentially skewed
- Fix approach: Use proper IDF formula: `idf = math.log(total_categories / (1 + docs_containing_token))`

**Encoding Error in Read Operations:**
- Issue: Some `read_text()` calls missing encoding specification; inconsistent use of `errors="replace"`
- Files: `src/corpus_analyzer/classifiers/document_type.py` (line 293 - no encoding), `src/corpus_analyzer/llm/unified_rewriter.py` (line 300, 357 - partial use)
- Impact: Platform-dependent behavior; potential data corruption on non-UTF-8 systems; inconsistent truncation handling
- Fix approach: Standardize all file reads to `read_text(encoding="utf-8", errors="replace")`

**CLI Vulnerability: Unsafe Type Coercion in Rewrite Category:**
- Issue: CLI accepts `category` as string but may have unchecked enum conversion
- Files: `src/corpus_analyzer/cli.py` (line 285-291)
- Trigger: Provide invalid category value like `--category invalid_category`
- Impact: Graceful error handling exists, but no validation of category enum before processing; wasted work
- Fix approach: Validate category enum at CLI argument parsing level using Typer's Choice type

## Security Considerations

**Unvalidated LLM Output Paths:**
- Risk: Rewritten documents written to paths derived from `DocumentCategory.value` enum, but no validation of output_dir parameter
- Files: `src/corpus_analyzer/llm/unified_rewriter.py` (line 353-354)
- Current mitigation: Output directory created with `mkdir(parents=True, exist_ok=True)` which is safe, but directory traversal via category name not prevented
- Recommendations: (1) Validate category is from known enum, (2) sanitize output filenames, (3) use safe path joining (already done via `/`)

**Ollama Client Exception Suppression:**
- Risk: All exceptions in Ollama client suppressed with bare `except Exception` blocks
- Files: `src/corpus_analyzer/llm/ollama_client.py` (lines 72-73, 80-81)
- Current mitigation: Returns False/empty list, fails gracefully
- Recommendations: Log suppressed exceptions at DEBUG level for troubleshooting; consider specific exception types (ConnectionError, TimeoutError)

**Environment Variable Exposure in Prompts:**
- Risk: Full document content (potentially containing comments with secrets) sent to Ollama without sanitization
- Files: `src/corpus_analyzer/llm/unified_rewriter.py` (line 300), `src/corpus_analyzer/llm/rewriter.py` (line 262)
- Current mitigation: Truncation to 12000 characters, but no pattern-based filtering
- Recommendations: Sanitize content to remove lines matching secret patterns (AWS_KEY, DATABASE_URL, etc.) before sending to LLM

## Performance Bottlenecks

**Full Document Content Truncation on Every Classification:**
- Problem: `classify_documents()` reads full file content for every document, then truncates to 12000 characters
- Files: `src/corpus_analyzer/classifiers/document_type.py` (lines 307-310), `src/corpus_analyzer/llm/unified_rewriter.py` (line 300)
- Current capacity: Works fine for small corpora; slow for >1000 documents
- Scaling path: (1) Cache computed classifications, (2) read only first/last N lines instead of full file, (3) use mmap for large files

**Database Query Without Indexes on Frequently Filtered Columns:**
- Problem: Queries on `category` and `file_type` use indexes, but queries on `is_gold_standard` and `domain_tags` (JSON LIKE) do not
- Files: `src/corpus_analyzer/core/database.py` (lines 65-67, 226)
- Impact: Gold standard filtering and tag queries slow on large datasets (>10k documents)
- Improvement path: Add indexes: `CREATE INDEX idx_documents_is_gold_standard ON documents(is_gold_standard)`, use JSON_EACH for tag queries

**Sequential Document Processing Without Batch Operations:**
- Problem: `rewrite_category()` and `classify_documents()` process documents one-by-one
- Files: `src/corpus_analyzer/cli.py` (line 414), `src/corpus_analyzer/classifiers/document_type.py` (line 301)
- Current capacity: ~10 docs/sec on modern hardware; no parallelization
- Scaling path: Use `concurrent.futures.ThreadPoolExecutor` with max_workers=4-8, batch database updates

**Repeated Database Column Descriptor Fetches:**
- Problem: `get_document_by_id()` fetches cursor description by running empty SELECT query
- Files: `src/corpus_analyzer/core/database.py` (line 157)
- Impact: Extra database roundtrip per single document fetch; cumulative cost in loops
- Fix approach: Cache table schema at class initialization or use `PRAGMA table_info()`

## Fragile Areas

**Template-Based Rewriting Logic:**
- Files: `src/corpus_analyzer/llm/unified_rewriter.py` (lines 152-168, 281-314)
- Why fragile: Prompt structure highly dependent on template existence and format; fallback behavior not clearly documented; template injection possible if template contains special instructions
- Safe modification: (1) Validate template format before use, (2) document template contract, (3) escape template content in prompts
- Test coverage: Minimal - no tests for template loading, fallback behavior, or prompt injection scenarios

**Database Migration and Schema Assumptions:**
- Files: `src/corpus_analyzer/core/database.py` (lines 28-68, 249-272)
- Why fragile: Hard-coded column parsing using cursor.description; no migration framework; adding columns requires schema alter=True everywhere
- Safe modification: (1) Use type hints + ORM, (2) implement migration system, (3) validate schema on connection
- Test coverage: Only positive path tested; no tests for schema mismatches or corrupted JSON fields

**LLM Output Validation:**
- Files: `src/corpus_analyzer/llm/unified_rewriter.py` (lines 215-254)
- Why fragile: Regex-based validation of heading hierarchy, code blocks, frontmatter easily broken by model variations; no fallback if validation fails
- Safe modification: (1) Use lenient validation (warnings not failures), (2) document LLM model assumptions, (3) add model-specific prompt engineering
- Test coverage: No tests for quality validation edge cases (orphaned H3 without H2, unmatched code fences)

**Command-Line Interface Type Coercion:**
- Files: `src/corpus_analyzer/cli.py` (lines 233-356)
- Why fragile: Heavy use of `typer.confirm()` in loops without state persistence; file system side effects; no rollback on partial failure
- Safe modification: (1) Validate all inputs before any side effects, (2) implement transaction-like semantics for batch operations
- Test coverage: No tests for CLI commands

## Missing Critical Features

**No Duplicate Document Detection:**
- Problem: Same document added to corpus multiple times via different paths
- Blocks: Cannot analyze true corpus shape; classification statistics skewed; rewrite produces duplicates
- Workaround: Manual deduplication before extract
- Priority: High

**No Classification Confidence Thresholding:**
- Problem: Documents with low confidence (e.g., 0.4) classified as "UNKNOWN" would be better
- Blocks: Cannot filter uncertain classifications; analysis includes noise
- Workaround: Manual review of low-confidence results
- Priority: Medium

**No Rollback on Rewrite Failures:**
- Problem: If LLM rewrite fails mid-batch, no way to resume or revert
- Blocks: Large-scale rewrites risky
- Workaround: Track output files manually
- Priority: High

**No Streaming LLM Response Handling in CLI:**
- Problem: Rewrite operations block CLI output; user cannot see progress until LLM finishes
- Blocks: UX poor for slow models
- Workaround: Use streaming in code but not exposed in CLI
- Priority: Low

## Test Coverage Gaps

**LLM Integration Not Tested:**
- What's not tested: Ollama client, response parsing, prompt building, template loading
- Files: `src/corpus_analyzer/llm/ollama_client.py`, `src/corpus_analyzer/llm/unified_rewriter.py`
- Risk: Rewrite pipeline could be broken by model changes, and nobody would know until production
- Priority: High

**Database Schema Not Validated:**
- What's not tested: Schema migrations, JSON field serialization, foreign key constraints
- Files: `src/corpus_analyzer/core/database.py`
- Risk: Silent data loss if JSON parsing fails; orphaned chunks if document deletion not cascaded
- Priority: High

**CLI Integration Tests Missing:**
- What's not tested: Full end-to-end workflows (extract → classify → rewrite), error messages, file output
- Files: `src/corpus_analyzer/cli.py`
- Risk: User-facing commands untested; silent failures possible
- Priority: Medium

**Classification Edge Cases Not Covered:**
- What's not tested: Empty documents, documents with only code, heading-less documents, mixed languages
- Files: `src/corpus_analyzer/classifiers/document_type.py`
- Risk: Unexpected classification results on unusual inputs
- Priority: Medium

**Quality Scoring Validation Missing:**
- What's not tested: Quality report edge cases (no headings, zero code blocks), score calculation correctness
- Files: `src/corpus_analyzer/llm/unified_rewriter.py`, `src/corpus_analyzer/llm/quality_scorer.py`
- Risk: Quality metrics unreliable; cannot trust rewrite quality
- Priority: High

## Dependencies at Risk

**Ollama Python Client Stability:**
- Risk: `ollama` package is young, API changes possible; pinned version unknown
- Impact: Model updates could break rewrite pipeline
- Migration plan: Pin version explicitly in requirements, add integration tests with multiple model versions

**Pydantic v2 Migration Incomplete:**
- Risk: Some models use `field(default_factory=...)` but inconsistent use of `Field` from Pydantic
- Impact: Model serialization could fail on edge cases
- Migration plan: Audit all Pydantic models, use consistent validation decorators

---

*Concerns audit: 2026-02-23*
