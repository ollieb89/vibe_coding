# Requirements: Corpus

**Defined:** 2026-02-24
**Core Value:** Surface relevant agent files instantly — query an entire local agent library and get ranked, relevant results in under a second.

## v1.4 Requirements

Requirements for the Search Precision milestone. All map to roadmap phases.

### Search Filtering

- [ ] **FILT-01**: User can filter `corpus search` results below a threshold with `--min-score <float>` (default `0.0` — no filtering)
- [ ] **FILT-02**: `--min-score` help text documents the RRF score range (~0.009–0.033) so users can calibrate thresholds
- [ ] **FILT-03**: When `--min-score` filters all results, user sees a contextual hint: "No results above X.xxx. Run without --min-score to see available scores."

### API / MCP Parity

- [ ] **PARITY-01**: Python `search()` API accepts `sort_by` parameter (engine already supports it; wrapper does not currently forward it)
- [ ] **PARITY-02**: Python `search()` API accepts `min_score` parameter
- [ ] **PARITY-03**: MCP `corpus_search` tool accepts `min_score` parameter

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Search Filtering

- **FILT-04**: MCP `corpus_search` tool accepts `sort_by` parameter (agents rarely need explicit sort; deferred)
- **FILT-05**: Score normalisation to 0–1 range (only if UX testing shows consistent user confusion; per-query minmax is misleading for cross-query comparisons)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Percentage-style score display | RRF scores are rank-based, not similarity measures; normalising would be dishonest and break `--min-score` cross-query thresholds |
| `--sort score` alias | Redundant with `--sort relevance` which already orders by score descending |
| Score display in CLI | Already fully implemented in v1.3 — no work needed |
| `--sort` CLI flag | Already fully implemented in v1.3 — no work needed |
| Interactive `--min-score` tuning (TUI) | Significant complexity, niche audience — defer indefinitely |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FILT-01 | Phase 13 | Pending |
| FILT-02 | Phase 14 | Pending |
| FILT-03 | Phase 14 | Pending |
| PARITY-01 | Phase 14 | Pending |
| PARITY-02 | Phase 14 | Pending |
| PARITY-03 | Phase 14 | Pending |

**Coverage:**
- v1.4 requirements: 6 total
- Mapped to phases: 6
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-24*
*Last updated: 2026-02-24 — traceability confirmed during roadmap creation*
