# SPDX-License-Identifier: MIT
# Tests of examples/ch19/train_embedder.py (Listing 19.1, Volume 2, Section 19.3).
# Run from the repository root:  python -m pytest tests/
# The end-to-end CPU smoke run needs requirements/embedding-training.txt and RUN_EMBEDDER_SMOKE=1; it downloads
# sentence-transformers/all-MiniLM-L6-v2 (about 90 MB) unless EMBEDDER_SMOKE_MODEL names a local model folder.
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "examples" / "ch19"
FIXTURE = DIR / "triples.example.jsonl"
spec = importlib.util.spec_from_file_location("train_embedder", DIR / "train_embedder.py")
te = importlib.util.module_from_spec(spec)
spec.loader.exec_module(te)          # imports only the standard library at module level


def test_fixture_is_valid():
    triples = te.load_triples(FIXTURE)
    assert 10 <= len(triples) <= 20
    assert len({q for q, _, _ in triples}) == len(triples)
    assert all(p != n for _, p, n in triples)


def test_object_rows_and_errors(tmp_path):
    f = tmp_path / "t.jsonl"
    f.write_text(json.dumps({"anchor": "q", "positive": "p", "negative": "n"}) + "\n\n", encoding="utf-8")
    assert te.load_triples(f) == [("q", "p", "n")]
    f.write_text(json.dumps(["q", "", "n"]) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        te.load_triples(f)
    f.write_text("", encoding="utf-8")
    with pytest.raises(SystemExit):
        te.load_triples(f)


def test_split_holds_out_whole_questions():
    triples = te.load_triples(FIXTURE) + [(te.load_triples(FIXTURE)[0][0], "p2", "n2")]
    train, held = te.split(triples, 0.2, 42)
    assert {q for q, _, _ in train}.isdisjoint({q for q, _, _ in held})
    assert len(train) + len(held) == len(triples) and held


@pytest.mark.skipif(os.environ.get("RUN_EMBEDDER_SMOKE") != "1", reason="set RUN_EMBEDDER_SMOKE=1")
def test_cpu_smoke_run(tmp_path):
    import sentence_transformers  # noqa: F401  (opted in: a missing package is a failure, not a skip)
    r = subprocess.run([sys.executable, str(DIR / "train_embedder.py"), "--data", str(FIXTURE),
                        "--model", os.environ.get("EMBEDDER_SMOKE_MODEL", "sentence-transformers/all-MiniLM-L6-v2"), "--no-instruction",
                        "--epochs", "1", "--batch-size", "8", "--warmup-steps", "0",
                        "--precision", "fp32", "--output", str(tmp_path / "out")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-4000:]
    assert "held-out retrieval" in r.stdout
    assert (tmp_path / "out" / "config_sentence_transformers.json").exists()
