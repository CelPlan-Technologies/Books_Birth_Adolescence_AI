<!-- SPDX-License-Identifier: MIT -->
# Credentials and variables

One table for every secret and setting the companion files read. Real values never go into the repository: `.gitignore` excludes `.env`, `.env.*` (except `.env.example`), `toolchain/secrets/*` (except `*.example`), key files and kubeconfigs. Templates: [`.env.example`](../.env.example), [`toolchain/.env.example`](../toolchain/.env.example), [`toolchain/secrets/pg_pw.txt.example`](../toolchain/secrets/pg_pw.txt.example).

## The Rack key: one secret, three names

The Rack's model servers are protected by one shared key. Three programs read it under three names:

| Variable | Read by | Role | Value |
|---|---|---|---|
| `VLLM_API_KEY` | vLLM (`rack/serving/gpt-oss-120b.sh`, `examples/ch16/vllm-docker.sh` (Volume 1 companion package)) | Server: rejects requests without it | The Rack key |
| `RACK_KEY` | LiteLLM gateway (`gateway/litellm/config.yaml`, `api_key: os.environ/RACK_KEY`) | Client of the Rack, on behalf of all users | The same Rack key |
| `LLM_KEY` | Direct clients (`examples/ch16/chat.sh`, `examples/ch16/three_tiers.py` (Volume 1 companion package)) | The key a client presents | The Rack key for a direct, administrative call to a Rack server; a gateway key for an application |

Rules:

- Applications call the gateway, never a Rack server directly; only the gateway holds `RACK_KEY` (Chapter 35). The Volume 1 examples call the Rack directly to show the API; on a production Rack, `LLM_KEY` is a gateway key and the URL is the gateway's.
- Store the Rack key once, in a Kubernetes Secret in the namespaces of the model servers and of the gateway, and map it to `VLLM_API_KEY` and `RACK_KEY` with `env.valueFrom.secretKeyRef`. Rotate it by updating the Secret and restarting the servers and the gateway together.
- Pass the key in the environment, not on a command line, where `ps` shows it. vLLM reads `VLLM_API_KEY` by itself.
- The serving scripts stop with an error when their variables are unset (`${VAR:?}`); `chat.sh` stops when `LLM_KEY` is unset; `three_tiers.py` raises `KeyError` (the last two are in the Volume 1 companion package).
- A server without a key is for a single developer on 127.0.0.1 only. `vllm-docker.sh` publishes its port on 127.0.0.1 unless `VLLM_BIND` is set; never expose a keyless server as a shared endpoint.

## Other secrets

| Variable or file | Read by | Where it lives |
|---|---|---|
| `ANTHROPIC_KEY` | Gateway (`gateway/litellm/config.yaml`, `cloud/gateway-cloud.yaml`) | Gateway Secret only |
| AWS credentials for Bedrock | Gateway (`cloud/gateway-cloud.yaml`) | IAM Roles Anywhere certificates on the gateway (Section 34.5); no static keys |
| `OPENAI_API_KEY` | `box/bench/ttft.py` (default `--api-key`); `examples/ch16/three_tiers.py` (Volume 1 companion package) | Only for the cloud line of that example |
| `QDRANT_API_KEY` | `rack/rag/acl_filter.py` | Secret of the retrieval service |
| `AWS_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | vLLM `runai_streamer` loading from the internal object store (`rack/serving/gpt-oss-120b.sh`) | Secret of the model servers; read-only access to the model bucket |
| `MCPO_KEY` | mcpo and Open WebUI on the Box (`box/tools/mcpo.ps1`) | Windows user environment of the Box user, created by `mcpo.ps1 -Setup` |
| `toolchain/secrets/pg_pw.txt` | pgvector in `toolchain/compose.yaml` (`POSTGRES_PASSWORD_FILE`) | File on the Box, mode 600, ignored by Git |
| Hugging Face token | `hf` on the admin workstation (`toolchain/acquire-models.sh`) | `hf auth login`, read-only token; never on model servers |
| Registry pull credentials | Kubernetes (`toolchain/k8s-prereqs.example.yaml`) | `kubernetes.io/dockerconfigjson` Secret created from the command line |

## Settings that are not secrets

| Variable | Read by | Default |
|---|---|---|
| `RACK_URL` | `examples/ch16/chat.sh` (Volume 1 companion package) | `http://rack:8000` |
| `VLLM_BIND` | `examples/ch16/vllm-docker.sh` (Volume 1 companion package) | `127.0.0.1` |
| `HF_REPO`, `HF_REVISION`, `MODEL_DIR`, `MANIFEST` | `toolchain/acquire-models.sh rack` | none (required) except `MANIFEST` = `MODEL_DIR.sha256` |
| `GGUF_REPO`, `GGUF_QUANT` | `toolchain/acquire-models.sh box` | `GGUF_QUANT` = `Q4_K_M` |
| `HF_HUB_OFFLINE=1` | Model servers | Set in the serving container's environment (Section 31.8); `gpt-oss-120b.sh` sets it |
| `DOCLING_IMAGE`, `PGVECTOR_IMAGE` | `toolchain/compose.yaml` via `toolchain/.env` | Placeholders in `toolchain/.env.example` |
| `OLLAMA_*` | Ollama on the Box (`box/windows/ollama-env.ps1`) | Listing 32.1 |

## Secret scanning

`.pre-commit-config.yaml` runs detect-secrets against `.secrets.baseline` before each commit (`pip install pre-commit && pre-commit install`), and the CI workflow `.github/workflows/check.yml` runs the same scan on every push.
