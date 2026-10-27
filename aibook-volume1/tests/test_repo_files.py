# SPDX-License-Identifier: MIT
# Syntax and parsing checks for every program and configuration file of the companion repository.
# Run from the repository root:  python -m pytest tests/   (needs pyyaml)
import ast
import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", "venv", "node_modules", "__pycache__"}


def files(*patterns):
    out = []
    for pattern in patterns:
        out += [p for p in ROOT.rglob(pattern) if not SKIP & set(p.relative_to(ROOT).parts)]
    return sorted(out)


def ids(paths):
    return [str(p.relative_to(ROOT)) for p in paths]


PY = files("*.py")
YAML = files("*.yaml", "*.yml")
JSON = files("*.json")
SH = files("*.sh")


@pytest.mark.parametrize("path", PY, ids=ids(PY))
def test_python_syntax(path):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


@pytest.mark.parametrize("path", YAML, ids=ids(YAML))
def test_yaml_parses(path):
    docs = [d for d in yaml.safe_load_all(path.read_text(encoding="utf-8")) if d is not None]
    assert docs, "no YAML document"


@pytest.mark.parametrize("path", JSON, ids=ids(JSON))
def test_json_parses(path):
    json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", SH, ids=ids(SH))
def test_bash_syntax(path):
    r = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_secret_templates_are_not_ignored_and_secrets_are():
    """C02: the .example templates are committed, the real files are ignored."""
    if not shutil.which("git"):
        pytest.skip("git not installed")
    probe = [".env", ".env.local", ".env.example", "id_ed25519", "server.key"]
    r = subprocess.run(["git", "check-ignore", "--no-index", "--stdin", "-v", "-n"],
                       input="\n".join(probe), cwd=ROOT, capture_output=True, text=True)
    if r.returncode == 128:
        pytest.skip("not a Git working tree")
    ignored = {line.split("\t")[1] for line in r.stdout.splitlines()
               if line.split("\t")[0] != "::" and not line.split("\t")[0].split(":")[-1].startswith("!")}
    assert {".env", ".env.local", "id_ed25519", "server.key"} <= ignored
    assert ".env.example" not in ignored


# Files whose format cannot carry a comment, or whose content must stay byte for byte as it is (LICENSE.txt, SCOPE):
# JSON and JSON Lines, the workbooks, the detect-secrets baseline (JSON) and the expected outputs that the tests compare byte for byte. Every other file must carry the SPDX line.
NO_COMMENT_SUFFIXES = {".json", ".jsonl", ".xlsx"}
NO_COMMENT_FILES = {".secrets.baseline"}
NO_COMMENT_DIRS = ("Programs/expected/",)
LOCAL_STATE = {".pytest_cache"}


def test_spdx_lines():
    """C01, R12: every file whose format allows a comment names its license (Rego and Markdown included)."""
    missing = []
    for p in sorted(ROOT.rglob("*")):
        rel = p.relative_to(ROOT).as_posix()
        if not p.is_file() or (SKIP | LOCAL_STATE) & set(p.relative_to(ROOT).parts):
            continue
        if p.suffix in NO_COMMENT_SUFFIXES or rel in NO_COMMENT_FILES or rel.startswith(NO_COMMENT_DIRS):
            continue
        if "SPDX-License-Identifier: MIT" not in p.read_text(encoding="utf-8"):
            missing.append(rel)
    assert not missing, missing


def test_readme_tables_are_rectangular():
    """R12: every row of a README table has as many cells as its header."""
    bad = []
    for md in files("README.md"):
        cols = None
        for n, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            if not line.startswith("|"):
                cols = None
                continue
            cells = line.strip().strip("|").split(" | ")
            if cols is None:
                cols = len(cells)
            elif not set(line) <= set("|-: ") and len(cells) != cols:
                bad.append(f"{md.relative_to(ROOT)}:{n}: {len(cells)} cells, header has {cols}")
    assert not bad, bad
