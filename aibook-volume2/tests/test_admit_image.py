# SPDX-License-Identifier: MIT
# Control-flow tests for toolchain/admit-image.sh (Listing 31.3, Volume 2, Section 31.5), with command stubs.
# docker, cosign and the scanners are replaced by small scripts; jq and bash are real. These tests check what the
# script does on each path (stop before signing, or sign the scanned digest); they are not registry, Trivy or KMS
# integration tests. Run from the repository root:  python -m pytest tests/
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "toolchain" / "admit-image.sh"

pytestmark = pytest.mark.skipif(not (shutil.which("bash") and shutil.which("jq")), reason="needs bash and jq")

CHILD = "sha256:" + "a" * 64      # linux/amd64 child of the source index
ARM = "sha256:" + "b" * 64        # linux/arm64 child
WRAP = "sha256:" + "c" * 64       # digest of an index that wraps the child (what --prefer-index=true makes)
PIN = "@sha256:" + "d" * 64

# docker stub. STUB_SOURCE: index | single; STUB_SCAN: ok | fail; STUB_COPY: preserve | wrap
# ("wrap" stands for a copy that wraps the child in a new index, as imagetools create does by default).
DOCKER = r'''#!/usr/bin/env bash
echo "docker $*" >> "$STUB_LOG"
if [[ $1 == buildx && $2 == imagetools && $3 == inspect ]]; then
  ref=$4
  if [[ $ref == registry.internal/* ]]; then
    [[ -f $STUB_STATE ]] || exit 1
    printf '{"schemaVersion":2,"digest":"%s"}\n' "$(cat "$STUB_STATE")"
  elif [[ $STUB_SOURCE == single ]]; then
    printf '{"schemaVersion":2,"digest":"%s","config":{},"layers":[]}\n' "$CHILD"
  else
    printf '{"schemaVersion":2,"digest":"sha256:%064d","manifests":[' 9
    printf '{"digest":"%s","platform":{"os":"linux","architecture":"amd64"}},' "$CHILD"
    printf '{"digest":"%s","platform":{"os":"linux","architecture":"arm64"}}]}\n' "$ARM"
  fi
  exit 0
fi
if [[ $1 == buildx && $2 == imagetools && $3 == create ]]; then
  if [[ $STUB_COPY == wrap || " $* " != *" --prefer-index=false "* ]]; then
    echo "$WRAP" > "$STUB_STATE"
  else
    echo "$CHILD" > "$STUB_STATE"
  fi
  exit 0
fi
if [[ $1 == run ]]; then
  case "$*" in
    *trivy*) [[ $STUB_SCAN == ok ]]; exit ;;
    *syft*) echo '{"spdxVersion":"SPDX-2.3"}'; exit 0 ;;
  esac
fi
echo "docker stub: unexpected call: $*" >&2
exit 2
'''

COSIGN = r'''#!/usr/bin/env bash
echo "cosign $*" >> "$STUB_LOG"
exit 0
'''


def run(tmp_path, **env_over):
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    for name, body in (("docker", DOCKER), ("cosign", COSIGN)):
        f = bindir / name
        f.write_text(body)
        f.chmod(0o755)
    log = tmp_path / "calls.log"
    env = {
        "PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}",
        "HOME": str(tmp_path),
        "STUB_LOG": str(log),
        "STUB_STATE": str(tmp_path / "registry-digest"),
        "STUB_SOURCE": "index", "STUB_SCAN": "ok", "STUB_COPY": "preserve",
        "CHILD": CHILD, "ARM": ARM, "WRAP": WRAP,
        "KMS_KEY": "awskms:///alias/test",
        "TRIVY": "registry.internal/sec/trivy" + PIN,
        "SYFT": "registry.internal/sec/syft" + PIN,
    }
    env.update(env_over)
    env = {k: v for k, v in env.items() if v is not None}
    p = subprocess.run(["bash", str(SCRIPT)], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60)
    calls = log.read_text().splitlines() if log.exists() else []
    return p, calls


def signed(calls):
    return [c for c in calls if c.startswith("cosign sign")]


def test_success_preserves_digest_and_signs_it(tmp_path):
    p, calls = run(tmp_path)
    assert p.returncode == 0, p.stderr
    create = [c for c in calls if "imagetools create" in c]
    assert len(create) == 1 and "--prefer-index=false" in create[0]
    assert f"vllm/vllm-openai@{CHILD}" in create[0]
    assert signed(calls) == [f"cosign sign --yes --key awskms:///alias/test registry.internal/llm/vllm-openai@{CHILD}"]
    assert any(c.startswith("cosign verify") for c in calls)
    assert (tmp_path / f"vllm-{CHILD[7:]}.spdx.json").exists()


def test_index_wrapping_copy_stops_before_signing(tmp_path):
    p, calls = run(tmp_path, STUB_COPY="wrap")
    assert p.returncode == 1
    assert "not the scanned" in p.stderr
    assert not signed(calls)


def test_failed_scan_stops_before_copy(tmp_path):
    p, calls = run(tmp_path, STUB_SCAN="fail")
    assert p.returncode == 1
    assert not [c for c in calls if "imagetools create" in c]
    assert not signed(calls)


def test_single_manifest_source_is_refused(tmp_path):
    p, calls = run(tmp_path, STUB_SOURCE="single")
    assert p.returncode == 1
    assert "single manifest" in p.stderr
    assert not [c for c in calls if c.startswith("docker run")]


def test_expected_digest_mismatch_stops(tmp_path):
    p, calls = run(tmp_path, EXPECT="sha256:" + "e" * 64)
    assert p.returncode == 1
    assert not [c for c in calls if c.startswith("docker run")]


@pytest.mark.parametrize("var", ["KMS_KEY", "TRIVY", "SYFT"])
def test_missing_variable_stops(tmp_path, var):
    p, calls = run(tmp_path, **{var: None})
    assert p.returncode != 0
    assert not calls


def test_unpinned_tool_image_stops(tmp_path):
    p, calls = run(tmp_path, TRIVY="aquasec/trivy:latest")
    assert p.returncode == 1
    assert not calls
