#!/usr/bin/env bash
# Listing 33.2 — One general-assistant replica
# From "The Birth and Adolescence of Artificial Intelligence", Volume 2, Section 33.3. Illustrative: checked against the documentation of the versions in Appendix B (Volume 2), not run end to end as one system. Test in staging before use.
# SPDX-License-Identifier: MIT
#
# The container command of the replica. Required variables (docs/credentials.md):
#   VLLM_API_KEY      the Rack key; vLLM then rejects requests without it.
#                     The gateway sends the same value as RACK_KEY.
#   AWS_ENDPOINT_URL  the internal S3 endpoint of the model store, with its
#                     credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
#                     from a Kubernetes Secret, never from this file
set -euo pipefail
: "${VLLM_API_KEY:?set VLLM_API_KEY (the Rack key; see docs/credentials.md)}"
: "${AWS_ENDPOINT_URL:?set AWS_ENDPOINT_URL to the internal S3 endpoint}"
export HF_HUB_OFFLINE=1   # no Hub access at run time (Section 31.8)

# weights from the internal object store
exec vllm serve s3://models/gpt-oss-120b \
  --served-model-name rack-general \
  --max-model-len 131072 \
  --gpu-memory-utilization 0.92 \
  --max-num-seqs 64 \
  --load-format runai_streamer \
  --enable-auto-tool-choice \
  --tool-call-parser openai \
  --port 8000
# prefix caching is on by default (V1)
# the API key is read from VLLM_API_KEY (not put on
# the command line, where ps would show it)
# container requests: nvidia.com/gpu: 1
# readiness probe: GET /health
