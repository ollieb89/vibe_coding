.PHONY: install dev test lint format clean typecheck

install:
	uv sync

dev:
	uv run corpus-analyzer --help

test:
	uv run pytest -v

test-cov:
	uv run pytest --cov=corpus_analyzer --cov-report=html

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy src/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov
	rm -f corpus.sqlite

# Development helpers
extract-demo:
	uv run corpus-analyzer extract ../. --output demo.sqlite -e .md -e .py

classify-demo:
	uv run corpus-analyzer classify demo.sqlite

analyze-demo:
	uv run corpus-analyzer analyze demo.sqlite --output reports/
