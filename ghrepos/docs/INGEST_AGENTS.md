**Ingest Agents into Chroma**

- **Purpose:** Index the repository `agents/` (and similar folders) into a Chroma collection for semantic search and retrieval.
- **Script:** `ingest_agents.py` at repository root.

Quick start

1. Dry run (no upload):

```bash
python ingest_agents.py --source ./agents --collection vibe_agents --dry-run
```

2. Ingest into Chroma (requires Chroma server configured via chroma config in the chroma package):

```bash
python ingest_agents.py --source ./agents --collection vibe_agents
```

Development notes

- If you are running from this repo and the `chroma` package isn't installed, the script will try to use the local `../chroma/src` path. You can override with `--chroma-src /path/to/chroma/src`.
- Default chunking: `chunk-size=1000`, `chunk-overlap=200`, `batch-size=100`.

Next steps

- Run dry-run first to validate discovered files and estimated chunk counts.
- Start Chroma (or point the chroma config at your running service) before performing the actual ingestion.
