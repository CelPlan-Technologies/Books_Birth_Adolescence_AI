# SPDX-License-Identifier: MIT
# Tests of Programs/ch01_corpus_statistics.py (Volume 1, Chapter 1) on small synthetic corpora.
# Run from the repository root:  python -m pytest tests/
# The full-corpus regression runs only if NLTK_GUTENBERG_DIR names a folder with the 18 NLTK Gutenberg .txt files.
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROG = ROOT / "Programs" / "ch01_corpus_statistics.py"
EXPECTED = ROOT / "Programs" / "expected" / "ch01_corpus_statistics_seed1.txt"


def run(*args):
    return subprocess.run([sys.executable, "-I", str(PROG), *map(str, args)],
                          capture_output=True, text=True, encoding="utf-8")


def test_empty_folder_is_rejected(tmp_path):
    r = run(tmp_path)
    assert r.returncode == 2 and "no .txt files" in r.stderr


def test_tiny_corpus_is_rejected(tmp_path):
    (tmp_path / "a.txt").write_text("hello world", encoding="utf-8")
    r = run(tmp_path)
    assert r.returncode == 2 and "at least" in r.stderr


def test_small_corpus_reports_only_available_samples(tmp_path):
    text = "the captain of the white whale sat on the sea and the old man. " * 200
    (tmp_path / "a.txt").write_text(text, encoding="utf-8")
    r = run(tmp_path, "--encoding", "utf-8")
    assert r.returncode == 0, r.stderr
    table = r.stdout.split("Table 1.8")[1].split("Table 1.12")[0]
    letters = sum(c.isalpha() for c in text)
    sizes = [int(l.split("letters")[0].replace(",", "")) for l in table.splitlines() if "letters:" in l]
    assert sizes == [10, 100, 1000, letters]        # no 10,000-letter sample from 9,600 letters


def test_utf8_option(tmp_path):
    (tmp_path / "a.txt").write_text("café naïve über " * 50 + "the whale " * 100, encoding="utf-8")
    assert run(tmp_path, "--encoding", "utf-8").returncode == 0
    assert run(tmp_path).returncode == 0            # default latin-1 still reads UTF-8 bytes


@pytest.mark.skipif(not os.environ.get("NLTK_GUTENBERG_DIR"), reason="NLTK_GUTENBERG_DIR not set")
def test_book_corpus_output_unchanged():
    r = run(os.environ["NLTK_GUTENBERG_DIR"])
    assert r.returncode == 0, r.stderr
    assert r.stdout == EXPECTED.read_text(encoding="utf-8")
