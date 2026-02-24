"""Ollama embedding client for corpus-analyzer.

Provides connection validation, batch embedding, and model dimension detection
for Ollama's embedding API.
"""

from __future__ import annotations

import ollama

_DEFAULT_BATCH_SIZE = 8
_DEFAULT_MAX_CHARS = 2000


class OllamaEmbedder:
    """Client for generating text embeddings via Ollama.

    Attributes:
        model: Name of the embedding model to use (e.g., "nomic-embed-text").
        host: URL of the Ollama server.
    """

    def __init__(
        self,
        model: str,
        host: str = "http://localhost:11434",
        batch_size: int = _DEFAULT_BATCH_SIZE,
        max_chars: int = _DEFAULT_MAX_CHARS,
    ) -> None:
        """Initialize the embedder with model and host.

        Args:
            model: Name of the embedding model.
            host: URL of the Ollama server. Defaults to http://localhost:11434.
            batch_size: Max texts per Ollama API call. Defaults to 32.
            max_chars: Max characters per text before truncation. Defaults to 8000.
        """
        self.model = model
        self.host = host
        self._batch_size = batch_size
        self._max_chars = max_chars
        self._client = ollama.Client(host=host)

    def validate_connection(self) -> None:
        """Validate that Ollama is reachable.

        Raises:
            RuntimeError: If Ollama is not running or not reachable.
        """
        try:
            self._client.list()
        except Exception as e:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.host}. "
                f"Start Ollama with: ollama serve"
            ) from e

    def get_model_dims(self) -> int:
        """Get the dimension of the embedding model.

        Embeds a test string and returns the vector length.

        Returns:
            The dimension (length) of the embedding vectors.

        Raises:
            RuntimeError: If the model is not pulled.
        """
        try:
            response = self._client.embed(model=self.model, input=["test"])
            return len(response.embeddings[0])
        except Exception as e:
            error_msg = str(e).lower()
            if "not found" in error_msg:
                raise RuntimeError(
                    f"Model '{self.model}' not found. "
                    f"Pull it with: ollama pull {self.model}"
                ) from e
            raise

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts, splitting into sub-batches to avoid context limits.

        Texts are truncated to max_chars before embedding, and the list is split
        into sub-batches of batch_size to stay within Ollama's context window.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (each is a list of floats).
            Empty list if texts is empty.
        """
        if not texts:
            return []

        truncated = [t[: self._max_chars] for t in texts]
        all_embeddings: list[list[float]] = []
        for i in range(0, len(truncated), self._batch_size):
            batch = truncated[i : i + self._batch_size]
            response = self._client.embed(model=self.model, input=batch)
            all_embeddings.extend([list(vec) for vec in response.embeddings])
        return all_embeddings
