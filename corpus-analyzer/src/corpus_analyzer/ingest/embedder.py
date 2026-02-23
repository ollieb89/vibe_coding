"""Ollama embedding client for corpus-analyzer.

Provides connection validation, batch embedding, and model dimension detection
for Ollama's embedding API.
"""

from __future__ import annotations

import ollama


class OllamaEmbedder:
    """Client for generating text embeddings via Ollama.

    Attributes:
        model: Name of the embedding model to use (e.g., "nomic-embed-text").
        host: URL of the Ollama server.
    """

    def __init__(self, model: str, host: str = "http://localhost:11434") -> None:
        """Initialize the embedder with model and host.

        Args:
            model: Name of the embedding model.
            host: URL of the Ollama server. Defaults to http://localhost:11434.
        """
        self.model = model
        self.host = host
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
        """Embed a batch of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (each is a list of floats).
            Empty list if texts is empty.
        """
        if not texts:
            return []

        response = self._client.embed(model=self.model, input=texts)
        # Cast from Sequence[Sequence[float]] to list[list[float]]
        return [list(vec) for vec in response.embeddings]
