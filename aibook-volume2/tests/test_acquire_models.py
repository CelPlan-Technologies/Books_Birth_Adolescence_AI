# SPDX-License-Identifier: MIT
# Control-flow tests for toolchain/acquire-models.sh, box step (Listing 31.4, Volume 2, Section 31.8), with stubs:
# hf and ollama are small scripts, huggingface_hub is a fake module that returns fixed metadata. These tests check that
# the Box imports only a file whose hash matches the pinned revision; they do not contact the Hub or run Ollama.
# Run from the repository root:  python -m pytest tests/
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "toolchain" / "acquire-models.sh"
pytestmark = pytest.mark.skipif(not (shutil.which("bash") and shutil.which("sha256sum")),
                                reason="needs bash and sha256sum")

REV = "0123456789abcdef0123456789abcdef01234567"  # pragma: allowlist secret (a made-up commit hash)
FILE = "model-Q4_K_M.gguf"
GOOD = b"GGUF approved bytes"

HF = r'''#!/usr/bin/env bash
echo "hf $*" >> "$STUB_LOG"
# hf download REPO FILE --revision REV --local-dir DIR
dir=""; while [[ $# -gt 0 ]]; do [[ $1 == --local-dir ]] && dir=$2; shift; done
mkdir -p "$dir" && printf '%s' "$STUB_CONTENT" > "$dir/$STUB_FILE"
'''
OLLAMA = r'''#!/usr/bin/env bash
echo "ollama $* (cwd $(pwd))" >> "$STUB_LOG"
'''
FAKE_HUB = '''
import json, os
class _S:
    def __init__(self, d):
        self.rfilename, self.blob_id = d["name"], d.get("blob_id")
        self.lfs = type("L", (), {"sha256": d["sha256"]})() if d.get("sha256") else None
class HfApi:
    def model_info(self, repo, revision=None, files_metadata=False):
        m = json.loads(os.environ["STUB_META"])
        return type("I", (), {"sha": m["sha"], "siblings": [_S(d) for d in m["siblings"]]})()
'''


def run(tmp_path, content=GOOD, **env_over):
    bindir, fake = tmp_path / "bin", tmp_path / "fake"
    bindir.mkdir(exist_ok=True)
    (fake / "huggingface_hub").mkdir(parents=True, exist_ok=True)
    (fake / "huggingface_hub" / "__init__.py").write_text(FAKE_HUB)
    for name, body in (("hf", HF), ("ollama", OLLAMA)):
        (bindir / name).write_text(body)
        (bindir / name).chmod(0o755)
    py = bindir / "python3"
    if not py.exists():
        py.symlink_to(sys.executable)
    meta = {"sha": REV, "siblings": [
        {"name": FILE, "sha256": hashlib.sha256(GOOD).hexdigest(), "blob_id": "1" * 40},
        {"name": "model-Q8_0.gguf", "sha256": "2" * 64, "blob_id": "3" * 40}]}
    log = tmp_path / "calls.log"
    env = {"PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}", "HOME": str(tmp_path),
           "PYTHONPATH": str(fake), "STUB_LOG": str(log), "STUB_FILE": FILE,
           "STUB_CONTENT": content.decode(), "STUB_META": json.dumps(meta),
           "GGUF_REPO": "example/model-GGUF", "GGUF_REVISION": REV, "GGUF_FILE": FILE,
           "OLLAMA_NAME": "box-model"}
    env.update(env_over)
    env = {k: v for k, v in env.items() if v is not None}
    p = subprocess.run(["bash", str(SCRIPT), "box"], cwd=tmp_path, env=env, capture_output=True, text=True,
                       timeout=60)
    calls = log.read_text().splitlines() if log.exists() else []
    return p, calls


def test_box_imports_verified_file(tmp_path):
    p, calls = run(tmp_path)
    assert p.returncode == 0, p.stderr
    assert calls[0] == f"hf download example/model-GGUF {FILE} --revision {REV} --local-dir {tmp_path}/models/box-model"
    create = [c for c in calls if c.startswith("ollama create")]
    assert create == [f"ollama create box-model -f Modelfile (cwd {tmp_path}/models/box-model)"]
    assert (tmp_path / "models" / "box-model" / "Modelfile").read_text() == f"FROM ./{FILE}\n"
    assert hashlib.sha256(GOOD).hexdigest() in (tmp_path / "models" / "box-model.sha256").read_text()
    assert not [c for c in calls if c.startswith("ollama pull")]


def test_box_stops_on_hash_mismatch(tmp_path):
    p, calls = run(tmp_path, content=b"tampered")
    assert p.returncode != 0
    assert not [c for c in calls if c.startswith("ollama")]


@pytest.mark.parametrize("over", [{"GGUF_REVISION": "main"}, {"GGUF_REVISION": None}, {"GGUF_FILE": None},
                                  {"GGUF_FILE": "sub/x.gguf"}, {"OLLAMA_NAME": None}])
def test_box_refuses_bad_inputs(tmp_path, over):
    p, calls = run(tmp_path, **over)
    assert p.returncode != 0
    assert not calls
