# Listing 32.2 — Open WebUI with uv (PowerShell)
# From "The Birth and Adolescence of Artificial Intelligence", Volume 2, Section 32.2. Illustrative: checked against the documentation of the versions in Appendix B (Volume 2), not run end to end as one system. Test in staging before use.
# SPDX-License-Identifier: MIT
# once: a pinned installation in a fixed place
uv tool install --python 3.11 open-webui==0.11.4
# start script, run by Task Scheduler at sign-in:
$env:DATA_DIR = "D:\Box\webui"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
$env:RAG_EMBEDDING_ENGINE = "ollama"
$env:RAG_EMBEDDING_MODEL = "qwen3-embedding:0.6b"
$env:ENABLE_RAG_HYBRID_SEARCH = "True"
$env:RAG_RERANKING_MODEL = "BAAI/bge-reranker-v2-m3"
$env:RAG_TEXT_SPLITTER = "token"
$env:CHUNK_SIZE = "500"; $env:CHUNK_OVERLAP = "50"
$env:RAG_TOP_K = "30"; $env:RAG_TOP_K_RERANKER = "6"
open-webui serve --host 127.0.0.1 --port 8080
