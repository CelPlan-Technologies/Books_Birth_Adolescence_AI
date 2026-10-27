# SPDX-License-Identifier: MIT
# Offline tests of toolchain/verify_hub_hashes.py (companion to Listing 31.4, Volume 2, Section 31.8).
# Run from the repository root:  python -m pytest tests/
import hashlib
import importlib.util
import subprocess
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("vh", ROOT / "toolchain" / "verify_hub_hashes.py")
vh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vh)


@pytest.mark.skipif(not shutil.which("git"), reason="git not installed")
def test_git_blob_id_matches_git(tmp_path):
    f = tmp_path / "config.json"
    f.write_bytes(b'{"a": 1}\n')
    git = subprocess.run(["git", "hash-object", str(f)], capture_output=True, text=True).stdout.strip()
    assert vh.git_blob_id(f) == git


def test_verify_detects_changes(tmp_path):
    (tmp_path / "model.safetensors").write_bytes(b"weights")
    (tmp_path / "config.json").write_bytes(b"{}")
    (tmp_path / ".cache").mkdir()
    (tmp_path / ".cache" / "x").write_bytes(b"ignored")
    sib = [("model.safetensors", hashlib.sha256(b"weights").hexdigest(), None),
           ("config.json", None, vh.git_blob_id(tmp_path / "config.json"))]
    assert vh.verify(sib, str(tmp_path)) == []
    (tmp_path / "model.safetensors").write_bytes(b"tampered")
    (tmp_path / "extra.bin").write_bytes(b"")
    problems = vh.verify(sib + [("tokenizer.json", None, "0" * 40)], str(tmp_path))
    assert any("SHA-256 differs" in p for p in problems)
    assert any("missing" in p and "tokenizer.json" in p for p in problems)
    assert any("not in revision" in p and "extra.bin" in p for p in problems)


# third external review, R05: metadata without a usable hash must be an error, not a silent pass
@pytest.mark.parametrize("lfs_sha,blob_id", [
    (None, None),                 # both absent
    (None, ""),                   # empty blob id
    (None, "xyz"),                # not hex
    (None, "0" * 39),             # wrong length
    ("", None),                   # empty SHA-256
    ("ABC" + "0" * 61, None),     # upper case / not the Hub's form
    ("0" * 63, "0" * 40),         # short SHA-256 is not rescued by a blob id
])
def test_missing_or_malformed_hash_metadata_is_an_error(tmp_path, lfs_sha, blob_id):
    (tmp_path / "model.safetensors").write_bytes(b"arbitrary bytes")
    problems = vh.verify([("model.safetensors", lfs_sha, blob_id)], str(tmp_path))
    assert problems and "metadata" in problems[0]


def test_only_checks_named_file(tmp_path):
    (tmp_path / "m-Q4_K_M.gguf").write_bytes(b"q4")
    (tmp_path / "Modelfile").write_text("FROM ./m-Q4_K_M.gguf\n")
    sib = [("m-Q4_K_M.gguf", hashlib.sha256(b"q4").hexdigest(), "1" * 40),
           ("m-Q8_0.gguf", hashlib.sha256(b"q8").hexdigest(), "2" * 40)]
    assert vh.verify(sib, str(tmp_path), only=["m-Q4_K_M.gguf"]) == []
    assert any("not in revision" in p for p in vh.verify(sib, str(tmp_path), only=["m-Q5.gguf"]))
    (tmp_path / "m-Q4_K_M.gguf").write_bytes(b"tampered")
    assert any("SHA-256 differs" in p for p in vh.verify(sib, str(tmp_path), only=["m-Q4_K_M.gguf"]))
