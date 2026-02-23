"""Tests for corpus_analyzer.ingest.embedder — OllamaEmbedder.

Uses mocked ollama client to avoid live network calls.
"""

from unittest.mock import MagicMock, patch

import pytest

from corpus_analyzer.ingest.embedder import OllamaEmbedder


class TestOllamaEmbedderInit:
    """Tests for OllamaEmbedder initialization."""

    def test_stores_model_and_host(self) -> None:
        """Embedder stores model and host attributes."""
        embedder = OllamaEmbedder(model="nomic-embed-text", host="http://other:8080")
        assert embedder.model == "nomic-embed-text"
        assert embedder.host == "http://other:8080"

    def test_default_host(self) -> None:
        """Default host is http://localhost:11434."""
        embedder = OllamaEmbedder(model="test-model")
        assert embedder.host == "http://localhost:11434"


class TestValidateConnection:
    """Tests for validate_connection method."""

    def test_succeeds_when_ollama_reachable(self) -> None:
        """validate_connection succeeds when ollama.list() works."""
        embedder = OllamaEmbedder(model="test")

        with patch.object(embedder._client, "list") as mock_list:
            mock_list.return_value = {"models": []}
            embedder.validate_connection()  # Should not raise

    def test_raises_runtime_error_on_connection_refused(self) -> None:
        """validate_connection raises RuntimeError on ConnectionRefusedError."""
        embedder = OllamaEmbedder(model="test")

        with patch.object(embedder._client, "list", side_effect=ConnectionRefusedError()):
            with pytest.raises(RuntimeError) as exc_info:
                embedder.validate_connection()
            assert "Cannot connect to Ollama" in str(exc_info.value)
            assert "ollama serve" in str(exc_info.value)

    def test_raises_runtime_error_on_response_error(self) -> None:
        """validate_connection raises RuntimeError on ollama.ResponseError."""
        embedder = OllamaEmbedder(model="test")

        with patch.object(embedder._client, "list", side_effect=Exception("connection failed")):
            with pytest.raises(RuntimeError) as exc_info:
                embedder.validate_connection()
            assert "Cannot connect to Ollama" in str(exc_info.value)


class TestGetModelDims:
    """Tests for get_model_dims method."""

    def test_returns_embedding_length(self) -> None:
        """get_model_dims returns length of embedding vector."""
        embedder = OllamaEmbedder(model="nomic-embed-text")

        mock_response = MagicMock()
        mock_response.embeddings = [[0.1] * 768]

        with patch.object(embedder._client, "embed", return_value=mock_response):
            dims = embedder.get_model_dims()
            assert dims == 768

    def test_raises_runtime_error_on_model_not_found(self) -> None:
        """get_model_dims raises RuntimeError when model not found."""
        embedder = OllamaEmbedder(model="missing-model")

        # Create a mock exception that looks like ollama.ResponseError
        mock_error = Exception("model 'missing-model' not found")

        with patch.object(embedder._client, "embed", side_effect=mock_error):
            with pytest.raises(RuntimeError) as exc_info:
                embedder.get_model_dims()
            assert "not found" in str(exc_info.value).lower()
            assert "ollama pull" in str(exc_info.value)

    def test_embeds_test_string(self) -> None:
        """get_model_dims embeds 'test' to get dimensions."""
        embedder = OllamaEmbedder(model="test-model")

        mock_response = MagicMock()
        mock_response.embeddings = [[0.1] * 512]

        with patch.object(embedder._client, "embed", return_value=mock_response) as mock_embed:
            embedder.get_model_dims()
            mock_embed.assert_called_once_with(model="test-model", input=["test"])


class TestEmbedBatch:
    """Tests for embed_batch method."""

    def test_returns_embeddings_for_texts(self) -> None:
        """embed_batch returns embeddings matching input count."""
        embedder = OllamaEmbedder(model="test")

        mock_response = MagicMock()
        mock_response.embeddings = [[0.1] * 768, [0.2] * 768, [0.3] * 768]

        with patch.object(embedder._client, "embed", return_value=mock_response):
            texts = ["first", "second", "third"]
            embeddings = embedder.embed_batch(texts)

        assert len(embeddings) == 3
        assert len(embeddings[0]) == 768

    def test_returns_empty_list_for_empty_input(self) -> None:
        """embed_batch returns [] for empty texts list."""
        embedder = OllamaEmbedder(model="test")

        embeddings = embedder.embed_batch([])

        assert embeddings == []

    def test_calls_ollama_embed_with_correct_params(self) -> None:
        """embed_batch passes full list to ollama.embed()."""
        embedder = OllamaEmbedder(model="my-model")

        mock_response = MagicMock()
        mock_response.embeddings = [[0.1] * 768]

        with patch.object(embedder._client, "embed", return_value=mock_response) as mock_embed:
            embedder.embed_batch(["text one", "text two"])
            mock_embed.assert_called_once_with(model="my-model", input=["text one", "text two"])

    def test_single_text_returns_single_embedding(self) -> None:
        """embed_batch works with single text."""
        embedder = OllamaEmbedder(model="test")

        mock_response = MagicMock()
        mock_response.embeddings = [[0.5] * 768]

        with patch.object(embedder._client, "embed", return_value=mock_response):
            embeddings = embedder.embed_batch(["single text"])

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 768
