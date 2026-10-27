#!/usr/bin/env bash
# Launching vLLM in a container on one node
# From Volume 1, Section 16.5. Illustrative; test before use.
# SPDX-License-Identifier: MIT
#
# VLLM_API_KEY is required (docs/credentials.md): vLLM rejects requests
# without it. Clients send the same value as LLM_KEY.
# The port is published on 127.0.0.1 unless VLLM_BIND says otherwise; set
# VLLM_BIND=0.0.0.0 only on a Rack node reachable from the gateway alone.
set -euo pipefail
: "${VLLM_API_KEY:?set VLLM_API_KEY (the Rack key; see docs/credentials.md)}"
BIND="${VLLM_BIND:-127.0.0.1}"
# Launching vLLM in a container on one node
docker run --gpus all --ipc=host -p "${BIND}:8000:8000" \
  -e VLLM_API_KEY \
  -v /srv/models:/root/.cache/huggingface \
  vllm/vllm-openai:v0.31.0 \
  --model Qwen/Qwen3-32B-FP8 \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.90 \
  --kv-cache-dtype fp8 \
  --reasoning-parser qwen3
