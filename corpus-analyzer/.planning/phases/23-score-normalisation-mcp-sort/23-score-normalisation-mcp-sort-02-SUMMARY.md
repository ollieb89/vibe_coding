# MCP sort_by Parameter and Class Round-Trip Tests Summary

## Implementation Details

1. **SORT-01: MCP `sort_by` Parameter**
   - Added `sort_by: Optional[str] = None` to `corpus_search` tool signature in `src/corpus_analyzer/mcp/server.py`
   - Added `effective_sort_by` logic to resolve `sort_by` to `"relevance"` if omitted
   - Updated `engine.hybrid_search()` call to pass the `effective_sort_by`
   - Added two new tests to `tests/mcp/test_server.py`:
     - `test_corpus_search_sort_by_forwarded`: Confirms explicit `sort_by="construct"` is passed correctly
     - `test_corpus_search_sort_by_default_is_relevance`: Confirms omission passes `"relevance"`
   - Updated `test_corpus_search_passes_filters_to_hybrid_search` to expect `sort_by="relevance"` in assertions

2. **Round-Trip Tests Extension**
   - Extended `tests/ingest/test_round_trip.py` with two new parametrised cases for Python and TypeScript classes
   - Verified that `Greeter.__init__` and `Greeter.constructor` chunk names are correctly generated
   - Fixed text prefix assertions to match the actual indentation of the methods (`"    def __init__"` and `"    constructor"`)

## Testing Results

- All 24 tests passed across `tests/mcp/test_server.py` and `tests/ingest/test_round_trip.py`
- Lint checks with `ruff check src/corpus_analyzer/mcp/server.py` passed with no issues
- Round-trip class fixtures passed successfully, confirming that sub-chunking implementation from Phases 20-21 is complete and functioning properly for class methods

## Gaps & Known Issues

- None. The round-trip tests confirm that `chunk_name` and `chunk_text` emission for class methods is working as expected.
