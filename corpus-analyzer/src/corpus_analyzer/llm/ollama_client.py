"""Ollama client for local LLM integration."""

from typing import Iterator

import ollama
from pydantic import BaseModel

from corpus_analyzer.config import settings


class OllamaClient:
    """Client for interacting with local Ollama instance."""

    def __init__(
        self,
        host: str | None = None,
        model: str | None = None,
    ) -> None:
        """Initialize Ollama client."""
        self.host = host or settings.ollama_host
        self.model = model or settings.ollama_model
        self.client = ollama.Client(host=self.host)

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        """Generate a completion."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat(
            model=self.model,
            messages=messages,
            options={"temperature": temperature},
        )

        return response["message"]["content"]

    def generate_stream(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
    ) -> Iterator[str]:
        """Generate a completion with streaming."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        stream = self.client.chat(
            model=self.model,
            messages=messages,
            options={"temperature": temperature},
            stream=True,
        )

        for chunk in stream:
            if content := chunk.get("message", {}).get("content"):
                yield content

    def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            self.client.list()
            return True
        except Exception:
            return False

    def list_models(self) -> list[str]:
        """List available models."""
        try:
            response = self.client.list()
            return [m["name"] for m in response.get("models", [])]
        except Exception:
            return []
