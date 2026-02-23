# Pumpl AI Local

Machine learning infrastructure for the Pumpl fitness platform. Contains training scripts, inference server, and evaluation tools.

## Quick Start

```bash
# Environment setup
cd ml-local
pixi install && pixi shell

# Start inference server
pixi run serve

# Run training
pixi run train

# Run tests
pixi run test
```

## Repository Structure

```
ml-local/
├── src/                      # All Python code
│   ├── config/               # Path & MLflow configuration
│   ├── core/                 # Logging, GPU, errors, I/O
│   ├── data/                 # Data processing & generation
│   ├── training/             # LoRA fine-tuning with Unsloth
│   ├── inference/            # BitsAndBytes and vLLM servers
│   ├── evaluation/           # Model evaluation & metrics
│   ├── merging/              # Model merging
│   ├── quantization/         # AWQ quantization
│   ├── pipeline/             # End-to-end orchestration
│   ├── deployment/           # Model registry (MLflow)
│   ├── schemas/              # Pydantic models
│   ├── context/              # Runtime state management
│   └── utils/                # Utilities
│
├── data/                     # Training data
│   ├── raw/                  # Source datasets
│   ├── processed/            # Transformed data
│   ├── validated/            # Quality-checked data
│   └── workouts/             # Final training JSONL
│
├── models/                   # Model weights
│   ├── base/                 # Base models (Llama, Mistral)
│   │   ├── llama-3.1-8b-instruct/
│   │   └── mistral-7b-instruct/
│   └── adapters/             # LoRA adapters
│       ├── pumpl-lora-output-unsloth/
│       ├── pumpl-lora-workout-final-unsloth/
│       └── pumpl-merged-model/
│
├── tests/                    # Test suite
├── scripts/                  # Utility scripts
├── docs/                     # Documentation
└── outputs/                  # Training outputs (gitignored)
```

## Development Commands

```bash
# Inference server
pixi run serve              # Port 8000, 4-bit quantization
pixi run serve-dev          # With hot reload
pixi run serve-vllm         # High-throughput vLLM server

# Training
pixi run train              # Default training
pixi run train-full         # Full workout config
python -m src.training.train_lora_workout_unsloth --epochs 3

# Data processing
python -m src.data.generate_training_data --num_examples 500
python -m src.data.distill_from_claude --num_examples 100
python -m src.data.process_raw_data

# Evaluation
pixi run eval
python -m src.evaluation.evaluate_bnb_server

# Quality
pixi run test               # pytest tests/
pixi run lint               # ruff check
pixi run format             # ruff format
```

## Path Configuration

All paths are configurable via environment variables in `.env`. Default paths:

| Type | Default Path | Environment Variable |
|------|--------------|---------------------|
| Base Models | `./models/base/llama-3.1-8b-instruct` | `MODEL_PATH` |
| LoRA Adapters | `./models/adapters/pumpl-lora-output-unsloth` | `LORA_OUTPUT_UNSLOTH_PATH` |
| Training Data | `./data/workouts/` | `TRAINING_DATA_PATH` |
| Raw Data | `./data/raw/` | `DATA_RAW_PATH` |

See `src/config/paths.py` for all path functions.

## Integration with FastAPI

The inference server connects to the main FastAPI backend:

```
FastAPI (apps/api:8001) ──HTTP──> ML Server (ml-local:8000)
                                        │
                                        ▼
                                 models/base/
                                 models/adapters/
```

Set `BNB_SERVER_URL=http://localhost:8000` in `pumplai/apps/api/.env`.

## VRAM Requirements

| Server Type | VRAM | Use Case |
|-------------|------|----------|
| BNB 4-bit | 10-12GB | Production (RTX 3080+) |
| BNB 8-bit | 14-16GB | Better quality |
| AWQ | 5-6GB | Memory-constrained |
| vLLM | 16GB+ | High-throughput |

## External Dependencies

- CUDA 12.8+ with RTX 5070 Ti support (Blackwell sm_120)
- PyTorch nightly (2.8.0+) from `cu128` index
- Unsloth from git (latest)

## Submodule Workflow

This is a git submodule. Commit changes in two steps:

```bash
# 1. Commit in ml-local
cd ml-local
git add . && git commit -m "feat: improvement"
git push origin main

# 2. Update parent reference
cd ..
git add ml-local
git commit -m "chore: update ml-local"
```

## Documentation

- [CLAUDE.md](CLAUDE.md) - Claude Code guidance
- [docs/](docs/) - Full documentation
- [docs/models/](docs/models/) - Model documentation
- [docs/training/](docs/training/) - Training guides
- [docs/testing/](docs/testing/) - Testing documentation

## License

Private - Pumpl AI Platform
