#!/usr/bin/env bash
# Chat request to vLLM on the Rack (curl)
# From Volume 1, Section 16.4. Illustrative; test before use.
# SPDX-License-Identifier: MIT
#
# LLM_KEY is required (docs/credentials.md): the key this client presents,
# equal to the server's VLLM_API_KEY. RACK_URL defaults to the book's host.
set -euo pipefail
: "${LLM_KEY:?set LLM_KEY (see docs/credentials.md)}"
RACK_URL="${RACK_URL:-http://rack:8000}"
# Chat request to vLLM on the Rack
curl -N --fail-with-body --connect-timeout 10 --max-time 300 \
  "$RACK_URL/v1/chat/completions" \
  -H "Authorization: Bearer $LLM_KEY" \
  -H "Content-Type: application/json" \
  -d '{
  "model": "Qwen/Qwen3-32B-FP8",
  "messages": [
    {"role": "system",
     "content": "Answer only from the context."},
    {"role": "user",
     "content": "Context: ... Notice period?"}],
  "temperature": 0.7, "top_p": 0.8,
  "max_tokens": 400,
  "chat_template_kwargs": {"enable_thinking": false},
  "stream": true }'
