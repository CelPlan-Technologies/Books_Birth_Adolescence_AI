#!/usr/bin/env bash
# Listing 31.4 — Acquiring models at a pinned revision
# From "The Birth and Adolescence of Artificial Intelligence", Volume 2, Section 31.8. Illustrative: checked against the documentation of the versions in Appendix B (Volume 2), not run end to end as one system. Test in staging before use.
# SPDX-License-Identifier: MIT
#
# Complete version of Listing 31.4. The Rack and the Box steps are separate
# commands, and every value comes from a required variable, so that a
# forgotten placeholder stops the script instead of reaching the shell:
#
#   rack: HF_REPO=Qwen/Qwen3-32B HF_REVISION=<40-hex commit> \
#         MODEL_DIR=/srv/models/qwen3-32b ./acquire-models.sh rack
#   box:  GGUF_REPO=<owner>/<repo>-GGUF GGUF_REVISION=<40-hex commit> \
#         GGUF_FILE=<name>-Q4_K_M.gguf OLLAMA_NAME=<name> ./acquire-models.sh box
#
# HF_REVISION and GGUF_REVISION are the full commit hash shown under "Files and
# versions" on the Hub (or by `hf download` in its output), chosen when the
# model is admitted, never a branch name such as main.
#
# The Box takes the same path as the Rack: one GGUF file at an immutable
# revision, checked against the Hub's SHA-256, then imported into Ollama from
# the local file (Modelfile: FROM ./file.gguf). `ollama pull hf.co/<repo>:<tag>`
# is not used: a repository and a quantization tag are a mutable reference, and
# recording `ollama list` afterwards records what arrived without enforcing an
# approved revision. The box step needs bash, hf, python3 with huggingface_hub
# and the ollama CLI (on Windows: Git Bash or WSL with Ollama reachable; or run
# the same commands by hand). A model split across several GGUF files is not
# handled here.
set -euo pipefail

rack() {
  : "${HF_REPO:?set HF_REPO, e.g. Qwen/Qwen3-32B}"
  : "${HF_REVISION:?set HF_REVISION to the full 40-hex commit hash}"
  : "${MODEL_DIR:?set MODEL_DIR, e.g. /srv/models/qwen3-32b}"
  [[ "$HF_REVISION" =~ ^[0-9a-f]{40}$ ]] \
    || { echo "HF_REVISION must be a 40-hex commit hash" >&2; exit 2; }
  local manifest="${MANIFEST:-${MODEL_DIR%/}.sha256}"

  # Rack: admin workstation with Hub access
  hf auth whoami >/dev/null || hf auth login   # read-only token
  hf download "$HF_REPO" \
    --revision "$HF_REVISION" \
    --local-dir "$MODEL_DIR"
  # hash every file except the Hub's local cache, from inside the folder
  # (a subshell, so the caller's directory does not change)
  ( cd "$MODEL_DIR" &&
    find . -type f ! -path './.cache/*' -print0 | sort -z |
      xargs -0 sha256sum ) > "$manifest"
  # check the files against the Hub's own record of that revision:
  # weights (LFS/Xet) by their SHA-256, small Git files by their Git blob id
  python3 "$(dirname "$0")/verify_hub_hashes.py" \
    "$HF_REPO" "$HF_REVISION" "$MODEL_DIR"
  # keep the hash file with the release record
  echo "manifest: $manifest"
  # model servers: no Hub access at run time. Set HF_HUB_OFFLINE=1 in the
  # serving Deployment (env), not here: an export ends with this script.
}

box() {
  : "${GGUF_REPO:?set GGUF_REPO to <owner>/<repo>-GGUF}"
  : "${GGUF_REVISION:?set GGUF_REVISION to the full 40-hex commit hash}"
  : "${GGUF_FILE:?set GGUF_FILE to the .gguf file of the approved quantization}"
  : "${OLLAMA_NAME:?set OLLAMA_NAME, the name the Box uses for the model}"
  [[ "$GGUF_REVISION" =~ ^[0-9a-f]{40}$ ]] \
    || { echo "GGUF_REVISION must be a 40-hex commit hash" >&2; exit 2; }
  [[ "$GGUF_FILE" == *.gguf && "$GGUF_FILE" != */* ]] \
    || { echo "GGUF_FILE must be one .gguf file name, no folder" >&2; exit 2; }
  local dir="${GGUF_DIR:-$HOME/models/$OLLAMA_NAME}"
  local manifest="${MANIFEST:-${dir%/}.sha256}"

  # Box: one GGUF file at a pinned revision, checked, then imported into Ollama
  hf download "$GGUF_REPO" "$GGUF_FILE" \
    --revision "$GGUF_REVISION" \
    --local-dir "$dir"
  python3 "$(dirname "$0")/verify_hub_hashes.py" --only "$GGUF_FILE" \
    "$GGUF_REPO" "$GGUF_REVISION" "$dir"
  ( cd "$dir" && sha256sum "$GGUF_FILE" ) > "$manifest"
  # import the checked local file; add TEMPLATE/PARAMETER lines only if the
  # model card asks for them (compare with `ollama show --modelfile`)
  printf 'FROM ./%s\n' "$GGUF_FILE" > "$dir/Modelfile"
  ( cd "$dir" && ollama create "$OLLAMA_NAME" -f Modelfile )
  ollama list    # record the Ollama ID with the hash file and the revision
  echo "manifest: $manifest"
}

case "${1:-}" in
  rack) rack ;;
  box)  box ;;
  *) echo "usage: $0 rack|box   (variables: see the header)" >&2; exit 2 ;;
esac
