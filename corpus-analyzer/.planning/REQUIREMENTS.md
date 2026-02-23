# Requirements: Corpus

**Defined:** 2026-02-23
**Core Value:** Surface relevant agent files instantly — query an entire local agent library and get ranked, relevant results in under a second

## v1.1 Requirements

Requirements for v1.1 Search Quality milestone. Each maps to roadmap phases.

### Configuration

- [ ] **CONF-06**: User can specify `extensions = [".md", ".py"]` in a source block in corpus.toml to control which file types are indexed for that source
- [ ] **CONF-07**: `corpus index` skips files whose extension is not in the configured extensions list for that source
- [ ] **CONF-08**: When `extensions` is not configured for a source, a default allowlist applies covering common documentation and code types (`.md`, `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.yaml`, `.yml`, `.txt`) and excludes `.sh`, `.html`, `.json`, `.lock`, and binary files

### Classification

- [ ] **CLASS-04**: Classifier reads YAML frontmatter from `.md` files and uses `type`, `component_type`, or `tags` fields as construct classification signals
- [ ] **CLASS-05**: A file with a recognized frontmatter type declaration (e.g. `type: skill`) is classified with confidence ≥ 0.9

## v2 Requirements

Deferred to future milestones. Tracked but not in current roadmap.

### Search Precision

- **CHUNK-01**: Search results include line range (start/end) for the matching chunk
- **CHUNK-02**: Search result displays the matching chunk text snippet alongside the file path
- **CHUNK-03**: `corpus search --show-chunk` flag renders the matched chunk content in terminal output

### Indexing

- **IDX-01**: `.ts` and `.tsx` files are chunked using TypeScript AST analysis (function/class/interface boundaries) rather than line-based splitting

## Out of Scope

| Feature | Reason |
|---------|--------|
| Hosted/cloud index | Local-only — privacy, simplicity |
| Real-time file watching | Daemon complexity not justified yet |
| Web UI | CLI + MCP sufficient for target users |
| Score thresholding | Extension allowlist addresses root cause (junk files) more cleanly |
| Cross-source extension defaults | Per-source config is more flexible; global default handled by CONF-08 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CONF-06 | Phase 5 | Pending |
| CONF-07 | Phase 5 | Pending |
| CONF-08 | Phase 5 | Pending |
| CLASS-04 | Phase 6 | Pending |
| CLASS-05 | Phase 6 | Pending |

**Coverage:**
- v1.1 requirements: 5 total
- Mapped to phases: 5
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-23*
*Last updated: 2026-02-23 after roadmap creation (v1.1 phases 5–6 assigned)*
