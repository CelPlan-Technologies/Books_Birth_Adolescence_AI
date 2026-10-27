# SPDX-License-Identifier: MIT
# Syntax and parsing checks for every program and configuration file of the companion repository.
# Run from the repository root:  python -m pytest tests/   (needs pyyaml; PowerShell files are parsed only if pwsh is installed)
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
JSONL = files("*.jsonl")
SH = files("*.sh")
PS1 = files("*.ps1")


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


@pytest.mark.parametrize("path", JSONL, ids=ids(JSONL))
def test_jsonl_parses(path):
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert lines
    for line in lines:
        json.loads(line)


@pytest.mark.parametrize("path", SH, ids=ids(SH))
def test_bash_syntax(path):
    r = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


@pytest.mark.skipif(not shutil.which("pwsh"), reason="pwsh not installed")
@pytest.mark.parametrize("path", PS1, ids=ids(PS1))
def test_powershell_syntax(path):
    script = ("$e = $null; [void][System.Management.Automation.Language.Parser]::ParseFile("
              f"'{path}', [ref]$null, [ref]$e); if ($e) {{ $e | ForEach-Object {{ $_.ToString() }}; exit 1 }}")
    r = subprocess.run(["pwsh", "-NoProfile", "-NonInteractive", "-Command", script],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_secret_templates_are_not_ignored_and_secrets_are():
    """C02: the .example templates are committed, the real files are ignored."""
    if not shutil.which("git"):
        pytest.skip("git not installed")
    probe = ["toolchain/secrets/pg_pw.txt", ".env", ".env.local", "toolchain/.env",
             "toolchain/secrets/pg_pw.txt.example", ".env.example", "toolchain/.env.example",
             "id_ed25519", "server.key"]
    r = subprocess.run(["git", "check-ignore", "--no-index", "--stdin", "-v", "-n"],
                       input="\n".join(probe), cwd=ROOT, capture_output=True, text=True)
    if r.returncode == 128:
        pytest.skip("not a Git working tree")
    ignored = {line.split("\t")[1] for line in r.stdout.splitlines()
               if line.split("\t")[0] != "::" and not line.split("\t")[0].split(":")[-1].startswith("!")}
    assert {"toolchain/secrets/pg_pw.txt", ".env", ".env.local", "toolchain/.env",
            "id_ed25519", "server.key"} <= ignored
    assert not ignored & {"toolchain/secrets/pg_pw.txt.example", ".env.example", "toolchain/.env.example"}


# Files whose format cannot carry a comment, or whose content must stay byte for byte as it is (LICENSE.txt, SCOPE):
# JSON and JSON Lines, the workbooks, the detect-secrets baseline (JSON) and the prompt template reproduced exactly from
# the book. Every other file must carry the SPDX line.
NO_COMMENT_SUFFIXES = {".json", ".jsonl", ".xlsx"}
NO_COMMENT_FILES = {".secrets.baseline", "examples/ch17/prompt.txt"}
NO_COMMENT_DIRS = ()
LOCAL_STATE = {".pytest_cache"}


def test_spdx_lines():
    """C01, R12: every file whose format allows a comment names its license (Rego and Markdown included)."""
    missing = []
    for p in sorted(ROOT.rglob("*")):
        rel = p.relative_to(ROOT).as_posix()
        if not p.is_file() or (SKIP | LOCAL_STATE) & set(p.relative_to(ROOT).parts):
            continue
        if p.suffix in NO_COMMENT_SUFFIXES or rel in NO_COMMENT_FILES or (NO_COMMENT_DIRS and rel.startswith(NO_COMMENT_DIRS)):
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
