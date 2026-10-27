# Checking downloaded model files against the Hub's record (companion to Listing 31.4)
# From "The Birth and Adolescence of Artificial Intelligence", Volume 2, Section 31.8. Not printed in the book; called by acquire-models.sh.
# SPDX-License-Identifier: MIT
"""Verify a local model folder against the Hub's metadata for one revision.

    python verify_hub_hashes.py REPO REVISION FOLDER
    python verify_hub_hashes.py --only FILE [--only FILE ...] REPO REVISION FOLDER

Large files stored with LFS or Xet are compared by SHA-256 with the hash the
Hub records for them; small files kept in Git (config.json, tokenizer files)
by their Git blob id (SHA-1 of "blob <size>\\0" + content). Every file of the
revision must be present and match; extra local files (other than the Hub's
.cache folder) are reported. A file whose metadata carries no valid hash (no
64-hex SHA-256 and no 40-hex Git blob id) is an error, never a pass.
With --only, just the named files of the revision are checked (for one GGUF
file of a repository that holds many quantizations); each must exist in the
revision, and other local files are not reported.
Exit status 0 only if everything matches.
Needs huggingface_hub and read access to the Hub (admin workstation only).
"""
import hashlib
import os
import re
import sys

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
BLOB_RE = re.compile(r"^[0-9a-f]{40}$")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git_blob_id(path):
    h = hashlib.sha1(f"blob {os.path.getsize(path)}\0".encode())
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify(siblings, folder, only=None):
    """siblings: (name, lfs_sha256 or None, blob_id or None); returns a list of problems.
    only: if given, check just these names (each must be in the revision) and skip the extra-file scan."""
    problems, expected = [], set()
    if only is not None:
        names = {name for name, _, _ in siblings}
        problems += [f"not in revision  {n}" for n in sorted(set(only) - names)]
        siblings = [t for t in siblings if t[0] in set(only)]
    for name, lfs_sha, blob_id in siblings:
        expected.add(name)
        path = os.path.join(folder, name)
        if lfs_sha is not None:                       # LFS/Xet file: SHA-256 required
            if not (isinstance(lfs_sha, str) and SHA256_RE.match(lfs_sha)):
                problems.append(f"malformed SHA-256 in metadata  {name}")
                continue
        elif not (isinstance(blob_id, str) and BLOB_RE.match(blob_id)):
            problems.append(f"no valid hash in metadata  {name}")   # absent or malformed: never a pass
            continue
        if not os.path.isfile(path):
            problems.append(f"missing  {name}")
        elif lfs_sha is not None:
            if sha256(path) != lfs_sha:
                problems.append(f"SHA-256 differs  {name}")
        elif git_blob_id(path) != blob_id:
            problems.append(f"Git blob id differs  {name}")
    if only is not None:
        return problems
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if not (root == folder and d == ".cache")]
        for fn in files:
            rel = os.path.relpath(os.path.join(root, fn), folder).replace(os.sep, "/")
            if rel not in expected:
                problems.append(f"not in revision  {rel}")
    return problems


def main():
    args, only = sys.argv[1:], None
    while args[:1] == ["--only"] and len(args) >= 2:
        only = (only or []) + [args[1]]
        args = args[2:]
    if len(args) != 3:
        sys.exit(__doc__)
    repo, revision, folder = args
    from huggingface_hub import HfApi
    info = HfApi().model_info(repo, revision=revision, files_metadata=True)
    if info.sha != revision:
        sys.exit(f"the Hub resolved {revision} to {info.sha}; pin the full commit hash")
    siblings = [(s.rfilename, s.lfs.sha256 if s.lfs else None, s.blob_id)
                for s in info.siblings]
    problems = verify(siblings, folder, only)
    for p in problems:
        print(p)
    print(f"{len(only) if only else len(siblings)} files checked, {len(problems)} problems")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
