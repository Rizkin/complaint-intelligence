#!/usr/bin/env bash
# Run the LLM classification step in a container so it can reach the Windows Ollama via host.docker.internal.
# Usage: llm_docker.sh [--limit N]
set -euo pipefail
cd ~/complaint-intelligence
docker run --rm \
  --add-host=host.docker.internal:host-gateway \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  -e OLLAMA_MODEL="${OLLAMA_MODEL:-qwen3.5:2b}" \
  -v "$PWD":/work -w /work \
  python:3.12-slim bash -c "pip install -q pandas pyarrow requests 2>&1 | tail -1; python evals/classify.py llm $*"
