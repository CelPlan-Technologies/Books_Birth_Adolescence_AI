<!-- SPDX-License-Identifier: MIT -->
# The Birth and Adolescence of Artificial Intelligence — Volume 2 companion files

Companion files for **Volume 2: LLM System Architectures and Implementation**, by **Leonhard Korowajczuk**, first edition (October 2026). The companion files of Volume 1 (How Language Models Learn and Represent Human Knowledge) are distributed separately, in the Volume 1 companion package.

It holds the chapter workbooks of Volume 2, its code samples, and the configuration listings of Part VIII (the Box, the Rack, the Cloud tier and the gateway). The files follow the layout of Listing B.1 (Volume 2, Appendix B), except the `volume1/` folder, whose contents are in the Volume 1 companion package.

## Release: educational companion, ed1

This is release **ed1** of the **educational companion** to Volume 2, published with this edition (October 2026) at GitHub: XXX, as Volume 2, Appendix B describes. It helps the reader reproduce the calculations and examples of the books and see the configuration of Part VIII in full; it is **not a complete or tested reference implementation** of the Box, Rack, Cloud tier and gateway. The repository is **GitHub: XXX**, as the books say; errata and questions go to its issue tracker.

Included:

- **Workbooks:** all nineteen of Volume 2 (Chapters 17–35) in [`workbooks/`](workbooks/README.md), each reproducing the worked examples of its chapter.
- **Listings and code samples:** taken from the book text. They are illustrative and, where marked, abridged: each was checked against the documentation of the software versions in Table B.3 (Volume 2), but the complete system was **not run end to end** for the book. Where the review of the books found a defect, the file is the complete, corrected version and says so. Test every file in a staging environment before use, and pin the versions you test.
- **Supporting material:** dependency groups with tested versions (`requirements/`), a check suite (`tests/`, `.github/workflows/check.yml`), the credential contract (`docs/credentials.md`), deployment prerequisites and templates (`docs/deployment-prerequisites.md`, `*.example` files), and the provenance of the measured figures (`EVIDENCE.md`).

Not included, planned for later releases:

- the scheduled indexer (Section 32.4), Rack ingestion and fine-tuning jobs, operations dashboards and drills (folders `box/indexer`, `rack/rag` ingestion, `rack/finetune`, `ops` of Listing B.1);
- the gateway integration that makes the gateway an enforced boundary: the authentication and classification adapter, the policy-enforcement integration (LiteLLM calling OPA on every request and fallback), and end-to-end tests;
- a complete deployment graph: Kubernetes manifests for the vLLM replicas, the CPU embedding replica and the network policies of Chapters 33–35;
- the benchmark assets of Figure 20.3 (data generator, script, raw results; see `EVIDENCE.md`).

## Layout

```
aibook-volume2/
├── README.md         this file
├── LICENSE.txt       MIT License (every file)
├── ERRATA.md         corrections, newest first
├── EVIDENCE.md       where the evidence for each measured figure lives
├── .env.example      template of the variables the files read (docs/credentials.md)
├── docs/             credentials.md, deployment-prerequisites.md
├── requirements/     dependency groups: demo, embedding-training, deploy-tools, check
├── .github/          workflows/check.yml (the check suite)
├── workbooks/        Volume 2 workbooks, Ch17–Ch35 (see workbooks/README.md)
├── examples/         code samples of Chapters 17–28 (Tables B.1 and B.2)
├── toolchain/        Chapter 31
├── box/              Chapter 32: windows/, tools/, bench/
├── rack/             Chapter 33: cluster/, serving/, rag/
├── cloud/            Chapter 34: egress proxy, gateway entries
├── gateway/          Chapter 35: litellm/, policy/, retrieval/
└── tests/            regression tests (pytest)
```

## Files

| File | Source | Content | Where in the book |
|---|---|---|---|
| `examples/ch28/licenses.py` | Listing 28.1 | Collect license and size metadata | Volume 2, Section 28.8 |
| `gateway/policy/matrix.yaml` | Listing 30.1 | Routing matrix as policy data; `route.rego` reads its `destinations` table as `data.destinations` | Volume 2, Section 30.3 |
| `gateway/policy/audit-record.json` | Listing 30.2 | One audit record (abridged) | Volume 2, Section 30.5 |
| `toolchain/compose.yaml` | Listing 31.1 | Optional Box services (compose.yaml, run in WSL2); needs `toolchain/.env` and `toolchain/secrets/pg_pw.txt` (templates below) | Volume 2, Section 31.2 |
| `toolchain/embed.yaml` | Listing 31.2 | The embedding service on the Rack (embed.yaml), with a readiness probe and `HF_HUB_OFFLINE=1` added | Volume 2, Section 31.4 |
| `toolchain/admit-image.sh` | Listing 31.3 | Admitting an image to the internal registry (complete version: stops on any failed step, keeps the single-platform manifest on copy with `--prefer-index=false`, signs only the scanned digest; the source tag must be an index) | Volume 2, Section 31.5 |
| `toolchain/acquire-models.sh` | Listing 31.4 | Acquiring models at a pinned revision (complete version: required variables, separate `rack` and `box` commands; both download at a pinned 40-hex revision and check hashes against the Hub; the Box imports the checked GGUF file into Ollama with a Modelfile) | Volume 2, Section 31.8 |
| `box/windows/ollama-env.ps1` | Listing 32.1 | Ollama settings (PowerShell; complete version: `-Setup`, restart Ollama, then `-Pull`) | Volume 2, Section 32.2 |
| `box/windows/openwebui.ps1` | Listing 32.2 | Open WebUI with uv (PowerShell) | Volume 2, Section 32.2 |
| `box/tools/mcpo.ps1` | Listing 32.3 | Local files as a tool (mcpo; complete version: `-Setup` once, `-Start` at sign-in, key validated; read-only note) | Volume 2, Section 32.5 |
| `box/bench/ttft.py` | Listing 32.4 | Measuring TTFT and decode speed (complete version: command line, warm-up, repeated runs, median and percentiles; one request at a time, not a goodput load test) | Volume 2, Section 32.7 |
| `rack/cluster/gpu-operator.sh` | Listing 33.1 | Installing the GPU Operator | Volume 2, Section 33.2 |
| `rack/serving/gpt-oss-120b.sh` | Listing 33.2 | One general-assistant replica (requires `VLLM_API_KEY` and `AWS_ENDPOINT_URL`) | Volume 2, Section 33.3 |
| `rack/rag/acl_filter.py` | Listing 33.3 | The permission filter in every search | Volume 2, Section 33.4 |
| `cloud/egress-squid.conf` | Listing 34.1 | Egress proxy allow-list (Squid, abridged) | Volume 2, Section 34.4 |
| `cloud/gateway-cloud.yaml` | Listing 34.2 | Cloud deployments in the gateway (LiteLLM, abridged) | Volume 2, Section 34.5 |
| `gateway/litellm/config.yaml` | Listing 35.1 | Three tiers behind one API | Volume 2, Section 35.1 |
| `gateway/policy/route.rego` | Listing 35.2 | Routing policy in Rego (excerpt) | Volume 2, Section 35.1 |
| `gateway/policy/route_test.rego` | Tests | Policy tests: every cell of Table 30.5, mixed classes, empty or unknown classes and destinations | Volume 2, Section 35.1 |
| `gateway/retrieval/rrf.py` | Listing 35.3 | Fusing ranked lists by rank (RRF) (complete version: labels of one chunk united across tiers, stable identities, every occurrence checked and its labels kept, one vote per list) | Volume 2, Section 35.2 |
| `examples/ch19/train_embedder.py` | Listing 19.1 | Fine-tuning an embedder (Sentence Transformers 5.4–6.1; complete version: `--data` path, validation, precision by hardware, held-out retrieval evaluation) | Volume 2, Section 19.3 |
| `examples/ch19/triples.example.jsonl` | Fixture | 20 synthetic [question, positive, negative] triples for a smoke run of Listing 19.1 | Volume 2, Section 19.3 |
| `examples/ch17/prompt.txt` | Code sample | RAG prompt template (system and user messages) | Volume 2, Section 17.6 |
| `examples/ch23/tool.json` | Code sample | A tool definition (OpenAI-compatible format) | Volume 2, Section 23.1 |
| `toolchain/verify_hub_hashes.py` | Companion | Checks downloaded model files against the Hub's SHA-256 and Git blob ids for one revision; a file without a valid hash in the metadata is an error; `--only` for one file (called by `acquire-models.sh`) | Volume 2, Section 31.8 |
| `toolchain/k8s-prereqs.example.yaml` | Template | Namespace `retrieval` and `model-store` PVC for `embed.yaml`; registry pull secret | Volume 2, Sections 31.4, 33.6 |
| `toolchain/.env.example` | Template | Image digests read by `compose.yaml` | Volume 2, Section 31.2 |
| `toolchain/secrets/pg_pw.txt.example` | Template | How to create the pgvector password file | Volume 2, Section 31.2 |
| `.env.example` | Template | Every variable the files read, with the Rack-key mapping | — |
| `docs/credentials.md` | Companion | Secret and variable contract (`VLLM_API_KEY`, `RACK_KEY`, `LLM_KEY` and the others) | Volume 2, Chapters 31–35 |
| `docs/deployment-prerequisites.md` | Companion | Prerequisites and checks for `compose.yaml` and `embed.yaml` | Volume 2, Chapter 31 |
| `requirements/*.txt` | Companion | Dependency groups with tested exact versions: `demo`, `embedding-training`, `deploy-tools`, `check` | — |
| `EVIDENCE.md` | Companion | Provenance of the measured figures (Figure 20.3, published GB10 benchmarks) | Volume 2, Chapters 20, 28, 32 |
| `tests/test_repo_files.py`, `tests/test_train_embedder.py`, `tests/test_verify_hub_hashes.py`, `tests/test_admit_image.py`, `tests/test_acquire_models.py` | Tests | Parsing of every file, `.gitignore` and SPDX rules; Listing 19.1 data handling; hash checks; Listing 31.3 and 31.4 control flow with command stubs | — |
| `.github/workflows/check.yml`, `.pre-commit-config.yaml`, `.secrets.baseline` | Companion | The check suite and the secret scan (detect-secrets) | — |

Notes:

- `gateway/policy/audit-record.json` is an abridged example; JSON allows no comments, so its note is here.
- `examples/ch17/prompt.txt` is the RAG prompt template of Section 17.6, reproduced exactly.
- Dependency groups: `pip install -r requirements/demo.txt` (CPU examples), `requirements/embedding-training.txt` (Listing 19.1), `requirements/deploy-tools.txt` (admin workstation), `requirements/check.txt` (tests).
- Listing 33.2 is a `vllm serve` command, so it is stored as `rack/serving/gpt-oss-120b.sh`.

## Tests

- `python -m pytest tests/` runs the regression tests, among them `tests/test_rrf.py` (Listing 35.3: a passage labeled R4 by one tier and R1 by another keeps R4; identity conflicts, unlabeled passages and repeated entries, within one list as well as across lists) and `tests/test_ttft.py` (Listing 32.4, with mocked streams: one-event replies, mixed units, invalid counts; needs the `openai` package). No server or GPU is needed.
- `opa test -v gateway/policy/route.rego gateway/policy/route_test.rego gateway/policy/matrix.yaml` tests the routing policy (OPA 1.21). Name the files: loading the whole `gateway/policy/` folder also loads `audit-record.json` as data, which fails with a merge error.
- `tests/test_admit_image.py` runs `toolchain/admit-image.sh` with command stubs for docker and cosign (real bash and jq): a successful copy that keeps the scanned digest and is signed, an index-wrapping copy that stops before signing, a failed scan, a single-manifest source, a changed digest, missing variables. `tests/test_acquire_models.py` does the same for the Box step of `acquire-models.sh` (a hash mismatch stops before Ollama). These test control flow only, not a registry, Trivy, a KMS key, the Hub or Ollama.
- `tests/test_repo_files.py` parses every Python, YAML, JSON and JSON Lines file, runs `bash -n` on every shell script and parses the PowerShell scripts when `pwsh` is installed; it also checks the `.gitignore` secret rules, the SPDX lines (every file that can carry a comment, Rego and Markdown included) and that every README table row has as many cells as its header. `tests/test_train_embedder.py` and `tests/test_verify_hub_hashes.py` need no network.
- Expected skips. A plain `python -m pytest tests/` skips one test by design: the Listing 19.1 CPU training smoke run (set `RUN_EMBEDDER_SMOKE=1` with `requirements/embedding-training.txt` installed; `EMBEDDER_SMOKE_MODEL` may name a local model). Without `pwsh`, the three PowerShell parses are skipped as well. `pytest -rs` lists every skip with its reason.
- `.github/workflows/check.yml` has two jobs. `check` runs all of the above except the optional test, plus `opa test` with the files named, `docker compose config` on `toolchain/compose.yaml`, an offline schema check of the Kubernetes manifests (kubeconform) and a detect-secrets scan. `embedder-smoke` installs the training group with CPU torch and runs the smoke run; it downloads `sentence-transformers/all-MiniLM-L6-v2` by name, not at a pinned revision, since the run checks code paths, not quality. The `embedder-smoke` job fails if its test is skipped.
- Local run before the split into two packages, 26 October 2026 (Python 3.13, PowerShell 7.5.4 for parsing, temporary Git copy): OPA 1.21.3: 31/31; `docker compose config`, kubeconform (4/4) and the secret scan passed. Rerun after the split, 27 October 2026 (Python 3.13, no PowerShell): 89 pytest tests passed and 4 skipped (the three PowerShell parses and the embedder smoke run), and the secret scan passed; OPA, `docker compose config` and kubeconform were not rerun, as their files did not change. The workflow itself has not yet run on GitHub; keep the log and pass/skip summary of its first run with the release.

## Versions

The software versions the book was written against are in Volume 2, Table B.3 (October 2026): among them vLLM 0.31, Ollama 0.40, Open WebUI 0.11.4, OPA 1.21.3, LiteLLM 1.83.7 or later, GPU Operator 26.7.2. Newer releases may change flags and defaults.

## Errata and contact

Report errors, or statements overtaken by events, through the issue tracker of this repository (GitHub: XXX). Corrections are listed in [`ERRATA.md`](ERRATA.md) and incorporated into later editions.

## License

MIT License for every file, workbooks included. See [`LICENSE.txt`](LICENSE.txt); every file that can carry a comment has an SPDX line (JSON, the workbooks and files reproduced byte for byte cannot; see LICENSE.txt). The text and figures of the book are not covered by this license.

© 2026 Leonhard Korowajczuk.
