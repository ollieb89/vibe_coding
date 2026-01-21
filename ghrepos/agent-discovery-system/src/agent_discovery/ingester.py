"""Chroma ingester for agent discovery system.

This module provides the ingestion layer for the agent discovery system,
integrating with the shared chroma_ingestion package for unified client
management and best practices.

Architecture:
- Uses shared Chroma client from chroma_ingestion package
- Agent-specific metadata transformation
- Integration with Agent model from agent_discovery
- Backward compatible with existing agent discovery workflows
"""

from typing import Any

from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

try:
    from chroma_ingestion.clients.chroma import get_chroma_client
except ImportError:
    # Fallback for environments without chroma_ingestion package
    import os
    import chromadb
    
    def get_chroma_client(
        host: str | None = None,
        port: int | None = None,
    ) -> chromadb.HttpClient:
        """Fallback Chroma client getter.
        
        Args:
            host: Chroma server host
            port: Chroma server port
            
        Returns:
            Chroma HttpClient instance
        """
        host = host or os.getenv("CHROMA_HOST", "localhost")
        port = port or int(os.getenv("CHROMA_PORT", "9500"))
        return chromadb.HttpClient(host=host, port=port)

from agent_discovery.models import Agent


class AgentIngester:
    """Ingests agents into Chroma for semantic discovery.
    
    Responsibilities:
    - Transform Agent models into Chroma-compatible format
    - Semantic chunking with context preservation
    - Metadata extraction and normalization
    - Batch processing with retry logic
    - Collection lifecycle management
    
    Integration:
    - Uses shared Chroma client from chroma_ingestion
    - Compatible with AgentIngester from chroma_ingestion.ingestion.agents
    - Provides agent_discovery-specific transformations
    """

    COLLECTION_NAME = "agents_discovery"
    DEFAULT_BATCH_SIZE = 50
    MAX_RETRY_ATTEMPTS = 3

    def __init__(
        self,
        collection_name: str | None = None,
        chunk_size: int = 1500,
        chunk_overlap: int = 300,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ):
        """Initialize ingester with shared Chroma client.

        Args:
            collection_name: Name of Chroma collection
            chunk_size: Tokens per chunk (default 1500)
            chunk_overlap: Token overlap between chunks (default 300)
            batch_size: Default batch size for operations (default 50)
        """
        self.collection_name = collection_name or self.COLLECTION_NAME
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.batch_size = batch_size

        # Use shared client for consistency
        self.client = get_chroma_client()
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={
                "description": "Agent discovery system - all agents, prompts, instructions",
                "hnsw:space": "cosine",
                "version": "1.0",
                "schema_version": "agent_discovery_v1",
            },
        )

        # Use Markdown splitter for agent files
        self.splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.MARKDOWN,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        
        # Ingestion statistics
        self._stats = {
            "total_ingested": 0,
            "total_chunks": 0,
            "failed_agents": 0,
            "batch_count": 0,
        }

    def ingest(
        self,
        agents: list[Agent],
        batch_size: int | None = None,
        verbose: bool = True,
        retry_failed: bool = True,
    ) -> tuple[int, int]:
        """Ingest agents into Chroma collection with resilience patterns.

        Args:
            agents: List of Agent objects to ingest
            batch_size: Chunks per batch upsert (uses instance default if None)
            verbose: Print progress messages
            retry_failed: Retry failed agent processing

        Returns:
            Tuple of (agents_processed, chunks_ingested)
            
        Raises:
            ValueError: If agents list is invalid
        """
        if agents is None:
            raise ValueError("Agents list cannot be None")
            
        if not agents:
            if verbose:
                print("❌ No agents to ingest")
            return 0, 0

        # Use instance default if not specified
        batch_size = batch_size or self.batch_size

        if verbose:
            print(f"📂 Ingesting {len(agents)} agents into '{self.collection_name}'")
            print(f"   Batch size: {batch_size}, Chunk size: {self.chunk_size}")

        documents: list[str] = []
        ids: list[str] = []
        metadatas: list[dict[str, Any]] = []
        agents_processed = 0
        failed_agents: list[tuple[Agent, Exception]] = []

        # Process agents with error tracking
        for agent in agents:
            try:
                # Validate agent has required fields
                if not agent.content:
                    if verbose:
                        print(f"  ⚠️  Skipping {agent.name}: No content")
                    continue

                # Create semantic chunks from content
                chunks = self.splitter.create_documents([agent.content])

                if chunks:
                    agents_processed += 1

                    for i, chunk in enumerate(chunks):
                        # Create unique deterministic ID
                        doc_id = self._create_document_id(agent, i)

                        # Build metadata for Chroma (must be string, int, float, bool)
                        chunk_metadata = self._build_metadata(agent, i, len(chunks))

                        documents.append(chunk.page_content)
                        ids.append(doc_id)
                        metadatas.append(chunk_metadata)
                else:
                    if verbose:
                        print(f"  ⚠️  No chunks created for {agent.name}")

            except Exception as e:
                failed_agents.append((agent, e))
                self._stats["failed_agents"] += 1
                if verbose:
                    print(f"  ⚠️  Error processing {agent.name}: {e}")

        # Batch upsert to Chroma with retry logic
        if documents:
            if verbose:
                print(f"🚀 Upserting {len(documents)} chunks in batches of {batch_size}...")

            successful_batches = 0
            failed_batches = 0

            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i : i + batch_size]
                batch_ids = ids[i : i + batch_size]
                batch_metas = metadatas[i : i + batch_size]

                batch_num = i // batch_size + 1
                success = self._upsert_batch_with_retry(
                    batch_docs, batch_ids, batch_metas, batch_num, verbose
                )

                if success:
                    successful_batches += 1
                    self._stats["batch_count"] += 1
                else:
                    failed_batches += 1

            # Update statistics
            self._stats["total_ingested"] += agents_processed
            self._stats["total_chunks"] += len(documents)

            if verbose:
                print(f"\n✅ Ingestion complete!")
                print(f"   Agents processed: {agents_processed}/{len(agents)}")
                print(f"   Chunks ingested: {len(documents)}")
                print(f"   Successful batches: {successful_batches}")
                if failed_batches > 0:
                    print(f"   Failed batches: {failed_batches}")
                if failed_agents:
                    print(f"   Failed agents: {len(failed_agents)}")

            return agents_processed, len(documents)

        if verbose:
            print("❌ No documents created")
        return agents_processed, 0

    def _create_document_id(self, agent: Agent, chunk_index: int) -> str:
        """Create deterministic document ID.
        
        Args:
            agent: Agent object
            chunk_index: Chunk index
            
        Returns:
            Unique document ID
        """
        # Use content hash for true uniqueness across renames
        return f"{agent.content_hash}:{chunk_index}"

    def _upsert_batch_with_retry(
        self,
        documents: list[str],
        ids: list[str],
        metadatas: list[dict[str, Any]],
        batch_num: int,
        verbose: bool,
    ) -> bool:
        """Upsert batch with exponential backoff retry.
        
        Args:
            documents: Document contents
            ids: Document IDs
            metadatas: Document metadata
            batch_num: Batch number for logging
            verbose: Enable logging
            
        Returns:
            True if successful, False otherwise
        """
        import time
        
        for attempt in range(self.MAX_RETRY_ATTEMPTS):
            try:
                self.collection.upsert(
                    documents=documents,
                    ids=ids,
                    metadatas=metadatas,
                )
                
                if verbose:
                    print(f"  ✓ Batch {batch_num} ({len(documents)} chunks)")
                return True
                
            except Exception as e:
                if attempt < self.MAX_RETRY_ATTEMPTS - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    if verbose:
                        print(f"  ⚠️  Batch {batch_num} failed (attempt {attempt + 1}), "
                              f"retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    if verbose:
                        print(f"  ❌ Batch {batch_num} failed after {self.MAX_RETRY_ATTEMPTS} "
                              f"attempts: {e}")
                    return False
        
        return False

    def _build_metadata(
        self,
        agent: Agent,
        chunk_index: int,
        total_chunks: int,
    ) -> dict[str, Any]:
        """Build Chroma metadata from agent.

        Chroma only supports string, int, float, bool values.

        Args:
            agent: Agent object
            chunk_index: Current chunk index
            total_chunks: Total chunks for this agent

        Returns:
            Metadata dictionary
        """
        return {
            # Core identity
            "agent_name": agent.name,
            "agent_type": agent.agent_type.value,
            "description": agent.description[:500] if agent.description else "",
            # Classification (comma-separated for lists)
            "category": agent.category.value,
            "tech_stack": ",".join(agent.tech_stack),
            "languages": ",".join(agent.languages),
            "frameworks": ",".join(agent.frameworks),
            # Discovery
            "complexity": agent.complexity.value,
            "use_cases": ",".join(agent.use_cases[:5]),
            "subjects": ",".join(agent.subjects),
            # Source tracking
            "source_path": agent.source_path,
            "source_collection": agent.source_collection,
            "content_hash": agent.content_hash,
            # Chunk tracking
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
        }

    def clear_collection(self, verbose: bool = True) -> None:
        """Clear all documents from the collection.

        Args:
            verbose: Print progress messages
        """
        try:
            # Delete and recreate collection
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description": "Agent discovery system - all agents, prompts, instructions",
                    "hnsw:space": "cosine",
                },
            )
            if verbose:
                print(f"🗑️  Cleared collection '{self.collection_name}'")
        except Exception as e:
            if verbose:
                print(f"⚠️  Error clearing collection: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive collection and ingestion statistics.

        Returns:
            Dictionary with collection and ingestion stats
        """
        try:
            count = self.collection.count()
            
            return {
                "collection_name": self.collection_name,
                "collection_metadata": self.collection.metadata,
                "total_chunks": count,
                "ingestion_stats": {
                    "total_agents_ingested": self._stats["total_ingested"],
                    "total_chunks_created": self._stats["total_chunks"],
                    "failed_agents": self._stats["failed_agents"],
                    "batch_count": self._stats["batch_count"],
                },
                "configuration": {
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                    "batch_size": self.batch_size,
                },
            }
        except Exception as e:
            return {
                "collection_name": self.collection_name,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    def get_health(self) -> dict[str, Any]:
        """Health check for ingester and Chroma connection.
        
        Returns:
            Health status dictionary
        """
        try:
            # Test connection by getting collection count
            count = self.collection.count()
            
            return {
                "status": "healthy",
                "collection_name": self.collection_name,
                "collection_count": count,
                "client_connected": True,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "collection_name": self.collection_name,
                "error": str(e),
                "error_type": type(e).__name__,
                "client_connected": False,
            }

    def reset_stats(self) -> None:
        """Reset ingestion statistics."""
        self._stats = {
            "total_ingested": 0,
            "total_chunks": 0,
            "failed_agents": 0,
            "batch_count": 0,
        }


class AgentRetriever:
    """Retrieve agents from Chroma for discovery."""

    def __init__(self, collection_name: str = "agents_discovery"):
        """Initialize retriever.

        Args:
            collection_name: Name of Chroma collection to query
        """
        self.collection_name = collection_name
        self.client = get_chroma_client()
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def search(
        self,
        query: str,
        n_results: int = 10,
        distance_threshold: float = 1.0,
        where: dict[str, Any] | None = None,
        min_score: float | None = None,
        subject_boost: float = 0.15,
    ) -> list[dict]:
        """Search for agents matching a query.

        Args:
            query: Natural language search query
            n_results: Number of results to return
            distance_threshold: Maximum distance to include (lower = more similar)
            where: Optional metadata filter
            min_score: Minimum score threshold (after boost)
            subject_boost: Score boost when query matches subjects metadata (0.0-0.3)

        Returns:
            List of result dictionaries
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results * 2,  # Over-fetch for filtering
                where=where,
            )

            # Normalize query terms for subject matching
            query_terms = set(query.lower().replace("-", " ").replace("_", " ").split())

            formatted: list[dict] = []
            if results["documents"] and results["documents"][0]:
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                    strict=False,
                ):
                    if dist <= distance_threshold:
                        base_score = max(0, 1 - dist)

                        # Apply subject boost if query terms match subjects metadata
                        boost = 0.0
                        subjects_str = meta.get("subjects", "")
                        if subjects_str and subject_boost > 0:
                            subjects = set(
                                s.strip().lower()
                                for s in subjects_str.replace("-", " ").replace("_", " ").split(",")
                            )
                            # Check for overlap between query terms and subjects
                            matches = query_terms & subjects
                            if matches:
                                # Boost proportional to match count (max 2 matches = full boost)
                                boost = min(len(matches) / 2, 1.0) * subject_boost

                        final_score = min(base_score + boost, 1.0)  # Cap at 1.0

                        if min_score is None or final_score >= min_score:
                            formatted.append(
                                {
                                    "document": doc,
                                    "metadata": meta,
                                    "distance": dist,
                                    "score": final_score,
                                    "base_score": base_score,
                                    "boost": boost,
                                }
                            )

            # Deduplicate by agent name (keep best match)
            seen_agents: set[str] = set()
            unique: list[dict] = []
            for result in formatted:
                agent_name = result["metadata"].get("agent_name", "")
                if agent_name not in seen_agents:
                    seen_agents.add(agent_name)
                    unique.append(result)

            return unique[:n_results]

        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []

    def search_by_category(
        self,
        category: str,
        n_results: int = 10,
    ) -> list[dict]:
        """Search for agents in a specific category.

        Args:
            category: Category to filter by
            n_results: Number of results

        Returns:
            List of matching agents
        """
        try:
            results = self.collection.get(
                where={"category": category},
                limit=n_results * 3,  # Over-fetch for deduplication
            )

            formatted: list[dict] = []
            if results["documents"]:
                for doc, meta in zip(
                    results["documents"],
                    results["metadatas"],
                    strict=False,
                ):
                    formatted.append(
                        {
                            "document": doc,
                            "metadata": meta,
                        }
                    )

            # Deduplicate by agent name
            seen_agents: set[str] = set()
            unique: list[dict] = []
            for result in formatted:
                agent_name = result["metadata"].get("agent_name", "")
                if agent_name not in seen_agents:
                    seen_agents.add(agent_name)
                    unique.append(result)

            return unique[:n_results]

        except Exception as e:
            print(f"❌ Category search failed: {e}")
            return []

    def search_by_type(
        self,
        agent_type: str,
        n_results: int = 20,
    ) -> list[dict]:
        """Search for agents of a specific type.

        Args:
            agent_type: Type to filter by (agent, prompt, instruction, chatmode)
            n_results: Number of results

        Returns:
            List of matching agents
        """
        try:
            results = self.collection.get(
                where={"agent_type": agent_type},
                limit=n_results * 3,
            )

            formatted: list[dict] = []
            if results["documents"]:
                for doc, meta in zip(
                    results["documents"],
                    results["metadatas"],
                    strict=False,
                ):
                    formatted.append(
                        {
                            "document": doc,
                            "metadata": meta,
                        }
                    )

            # Deduplicate
            seen_agents: set[str] = set()
            unique: list[dict] = []
            for result in formatted:
                agent_name = result["metadata"].get("agent_name", "")
                if agent_name not in seen_agents:
                    seen_agents.add(agent_name)
                    unique.append(result)

            return unique[:n_results]

        except Exception as e:
            print(f"❌ Type search failed: {e}")
            return []

    def get_all_agents(self, limit: int = 500) -> list[dict]:
        """Get all unique agents in the collection.

        Args:
            limit: Maximum number of agents to return

        Returns:
            List of unique agents (first chunk only)
        """
        try:
            # Get only first chunks (chunk_index = 0)
            results = self.collection.get(
                where={"chunk_index": 0},
                limit=limit,
            )

            formatted: list[dict] = []
            if results["documents"]:
                for doc, meta in zip(
                    results["documents"],
                    results["metadatas"],
                    strict=False,
                ):
                    formatted.append(
                        {
                            "document": doc[:500],  # Truncate for listing
                            "metadata": meta,
                        }
                    )

            return formatted

        except Exception as e:
            print(f"❌ Get all agents failed: {e}")
            return []
