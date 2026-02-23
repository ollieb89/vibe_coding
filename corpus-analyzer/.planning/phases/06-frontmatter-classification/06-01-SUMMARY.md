# Phase 06-01 Summary: Frontmatter Classification Implementation

## Overview
Successfully implemented frontmatter-first construct classification with confidence scoring. Files with explicit `type:` or `component_type:` frontmatter fields are now classified with high confidence (0.95), making `--construct` filtering reliably accurate. Tags provide a softer signal at 0.70. Rule-based classification remains the fallback.

## What Was Built

### ClassificationResult Dataclass
Added to `src/corpus_analyzer/search/classifier.py` (lines 23-35):

```python
@dataclass
class ClassificationResult:
    construct_type: str  # One of the recognized construct types
    confidence: float    # 0.0-1.0 confidence score
    source: str          # "frontmatter", "rule_based", or "llm"
```

Confidence values:
- **0.95**: Frontmatter `type:` or `component_type:` match
- **0.70**: Frontmatter `tags:` substring match
- **0.80**: LLM classification
- **0.60**: Rule-based classification
- **0.50**: Default documentation fallback

### classify_by_frontmatter() Function
New function that parses YAML frontmatter for construct type declarations:

1. **Type key priority**: `type: skill` → confidence 0.95
2. **Component type fallback**: `component_type: prompt` → confidence 0.95
3. **CamelCase alias**: `componentType` treated as `component_type`
4. **Case insensitivity**: Both keys and values are case-insensitive
5. **Tags matching**: Substring match in tags list → confidence 0.70
6. **Graceful degradation**: Malformed YAML or unknown values fall through silently

### Updated classify_file() Function
Changed return type from `str` to `ClassificationResult`. Priority order:

1. Frontmatter explicit types (highest priority)
2. Rule-based heuristic signals
3. LLM fallback for ambiguous files (if enabled)
4. Default to documentation

### Indexer Integration
Updated `src/corpus_analyzer/ingest/indexer.py` to extract `.construct_type` from `ClassificationResult` before storing in LanceDB chunks table.

## Test Coverage

### New Tests (12 added to `tests/search/test_classifier.py`)

**Frontmatter type tests:**
- `test_classify_frontmatter_type_skill` - explicit type key resolution
- `test_classify_frontmatter_type_case_insensitive` - case-insensitive matching
- `test_classify_frontmatter_component_type` - component_type key fallback
- `test_classify_frontmatter_camelcase_alias` - componentType alias support
- `test_classify_frontmatter_type_beats_component_type` - priority when both present

**Fallthrough tests:**
- `test_classify_frontmatter_unknown_value_fallthrough` - unknown type values
- `test_classify_frontmatter_nonstring_value_fallthrough` - numeric type values
- `test_classify_frontmatter_malformed_yaml_fallthrough` - invalid YAML handling

**Tags tests:**
- `test_classify_frontmatter_tags_substring_match` - tags substring matching
- `test_classify_frontmatter_tags_case_insensitive` - tags case insensitivity
- `test_classify_frontmatter_tags_ignored_when_type_resolves` - tags ignored when type present
- `test_classify_frontmatter_unmatched_tags_fallthrough` - unmatched tags fall through

### Updated Tests (8 existing tests)
All existing rule-based tests updated to assert against `.construct_type`, `.confidence`, and `.source` attributes instead of raw string comparison.

## Implementation Decisions

### Key Constraints Followed
- `type:` and `component_type:` are the ONLY high-confidence keys
- Case-insensitive for both keys and values
- `componentType` (camelCase) recognized as alias for `component_type`
- Unknown values fall through silently (no logging)
- Exact match only for construct type values (no plural normalization)
- Non-string values coerced to str, then attempted match
- Fixed 0.95 confidence for any frontmatter match (no boosting)
- `type:` beats `component_type:` when both present
- Tags: case-insensitive substring match (`construct in tag.lower()`)
- Tags confidence = 0.70
- Tags ignored when `type:` already resolved

### Backward Compatibility
The indexer previously called `classify_file()` and stored the `str` result. The implementation was updated to extract the `.construct_type` attribute from `ClassificationResult` for database storage, maintaining backward compatibility with the chunk schema.

## Verification

All 191 tests pass:
```bash
uv run pytest -v  # 191 passed
uv run ruff check src/corpus_analyzer/search/classifier.py  # clean
uv run mypy src/corpus_analyzer/search/classifier.py  # clean
```

## Files Modified

| File | Lines Changed | Description |
|------|---------------|-------------|
| `src/corpus_analyzer/search/classifier.py` | +85, -35 | Added ClassificationResult dataclass, classify_by_frontmatter(), updated classify_by_rules() and classify_file() |
| `tests/search/test_classifier.py` | +105, -35 | Added 12 new tests, updated 8 existing tests for ClassificationResult |
| `src/corpus_analyzer/ingest/indexer.py` | +2, -1 | Extract construct_type string from ClassificationResult |
| `tests/ingest/test_indexer.py` | +3, -2 | Updated mocks to return ClassificationResult objects |

## Commits

Suggested commit sequence:
1. `refactor(06-01): convert classifier returns to ClassificationResult dataclass`
2. `feat(06-01): implement explicit type and component_type frontmatter classification`
3. `feat(06-01): implement tags substring match for frontmatter classification`
4. `fix(06-01): update indexer and tests for ClassificationResult compatibility`
