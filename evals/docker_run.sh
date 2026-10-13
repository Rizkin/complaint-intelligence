#!/usr/bin/env bash
# Run any evals script inside a container that can reach the Windows Ollama (host.docker.internal).
# WSL cannot reach it directly: Ollama on Windows listens on its own loopback only.
# Usage: evals/docker_run.sh python evals/classify_decision.py --model tev1:0.8b-q8_0 --tag tev1_0.8b
set -euo pipefail
cd "$(dirname "$0")/.."
docker run --rm \
  --add-host=host.docker.internal:host-gateway \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  -v "$PWD":/work -w /work \
  python:3.12-slim bash -c "pip install -q pandas pyarrow requests 2>&1 | tail -1; $*"
