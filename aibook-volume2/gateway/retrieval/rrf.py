# Listing 35.3 — Fusing ranked lists by rank (RRF)
# SPDX-License-Identifier: MIT
# From "The Birth and Adolescence of Artificial Intelligence", Volume 2, Section 35.2. Illustrative: checked against the documentation of the versions in Appendix B (Volume 2), not run end to end as one system. Test in staging before use.
# This file is the complete version of the printed listing; tests/test_rrf.py holds its regression tests.
#
# Each passage p carries:
#   p.id      a stable, namespaced identity of one chunk of one version of one document, assigned at ingestion,
#             e.g. "sharepoint:eng/specs/radio.docx#c12@v7" — never a per-tier row number or a search rank
#   p.sha256  the SHA-256 of the chunk text, so that one identity cannot carry two different contents
#   p.labels  its classification labels (owner and content for a Box item; Section 30.3)
# The same chunk returned by two tiers is fused into one candidate, and its labels are the UNION of the labels
# every tier reported: a later list can add a class, never remove one, so a passage labeled R4 by one tier and R1
# by another counts as R4 and R1, and the policy then applies the most restrictive outcome (Listing 35.2).
# Fusion does not authorize: the permission filter runs in every search (Listing 33.3), and the gateway checks
# permissions again for the passages it keeps, before reranking and before generation.

CLASSES = {"R1", "R2", "R3", "R4", "R5"}
UNLABELED = "?"   # marks a passage some tier returned without labels; never a valid class


def rrf(lists, k=60, top=30):
    """Reciprocal rank fusion of ranked lists (one per tier).

    Returns (best, labels): the identities of the `top` best passages, highest fused score first (ties broken by
    identity, so the order is deterministic), and the union of the labels reported for each identity.
    Raises ValueError if one identity arrives with two different contents, in two lists or twice in one list.
    """
    score, labels, digest = {}, {}, {}
    for ranked in lists:                     # one per tier
        seen = set()
        for r, p in enumerate(ranked, 1):
            # every occurrence, a repeat within one list included, is checked and its labels are kept
            if digest.setdefault(p.id, p.sha256) != p.sha256:
                raise ValueError(f"identity conflict: {p.id}")   # fail closed
            # union, never overwrite; an empty label set is recorded as UNLABELED
            labels.setdefault(p.id, set()).update(p.labels or [UNLABELED])
            if p.id in seen:                 # a repeated entry gains no extra vote, nothing else
                continue
            seen.add(p.id)
            score[p.id] = score.get(p.id, 0.0) + 1 / (k + r)
    best = sorted(score, key=lambda i: (-score[i], i))[:top]
    return best, labels                      # best: reranker input


def classes_present(kept, labels, prompt_classes):
    """The set of classes for the policy: the prompt's classes and the labels of every passage kept after
    reranking. Fails closed on a passage with no label, an unknown label or a label UNLABELED from any tier."""
    present = set(prompt_classes)
    for i in kept:                           # passages kept after reranking
        if not labels.get(i) or not labels[i] <= CLASSES:
            raise ValueError(f"unlabeled or unknown label: {i}")   # fail closed
        present |= labels[i]
    return present                           # the policy decides per class
