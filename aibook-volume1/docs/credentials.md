<!-- SPDX-License-Identifier: MIT -->
# Credentials and variables (Volume 1, Chapter 16 examples)

The Chapter 16 examples call a model server on the Rack. Real values never go into the repository: `.gitignore` excludes `.env` and `.env.*` (except `.env.example`), key files and kubeconfigs. Template: [`.env.example`](../.env.example).

| Variable | Read by | Role | Value |
|---|---|---|---|
| `VLLM_API_KEY` | vLLM (`examples/ch16/vllm-docker.sh`) | Server: rejects requests without it | The Rack key |
| `LLM_KEY` | Direct clients (`examples/ch16/chat.sh`, `examples/ch16/three_tiers.py`) | The key a client presents | The Rack key for a direct, administrative call to a Rack server; a gateway key for an application |
| `OPENAI_API_KEY` | `examples/ch16/three_tiers.py` (the OpenAI client reads it) | Cloud line of that example only | Your OpenAI key |
| `RACK_URL` | `examples/ch16/chat.sh` | Address of the Rack server (not a secret) | Default `http://rack:8000` |
| `VLLM_BIND` | `examples/ch16/vllm-docker.sh` | Address on which the port is published (not a secret) | Default `127.0.0.1` |

Rules:

- The Volume 1 examples call the Rack directly to show the API. In production, applications call the gateway, never a Rack server directly, and `LLM_KEY` is a gateway key (Volume 2, Chapter 35).
- Pass keys in the environment, not on a command line, where `ps` shows them. vLLM reads `VLLM_API_KEY` by itself.
- `chat.sh` stops when `LLM_KEY` is unset, `vllm-docker.sh` when `VLLM_API_KEY` is unset, and `three_tiers.py` raises `KeyError`.
- A server without a key is for a single developer on 127.0.0.1 only. `vllm-docker.sh` publishes its port on 127.0.0.1 unless `VLLM_BIND` is set; never expose a keyless server as a shared endpoint.
