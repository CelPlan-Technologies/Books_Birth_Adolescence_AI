# Regression tests for gateway/retrieval/rrf.py (Listing 35.3, Volume 2, Section 35.2).
# SPDX-License-Identifier: MIT
# Run from the repository root:  python -m pytest tests/
# RRF_IMPL=<path to a .py file> runs the same tests against another implementation (for example, the printed listing).
import hashlib
import importlib.util
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_IMPL = os.environ.get("RRF_IMPL") or str(Path(__file__).resolve().parents[1] / "gateway" / "retrieval" / "rrf.py")
_spec = importlib.util.spec_from_file_location("rrf_under_test", _IMPL)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
rrf, classes_present = _mod.rrf, _mod.classes_present


def P(id, labels, text=None):
    text = id if text is None else text
    return SimpleNamespace(id=id, labels=labels, sha256=hashlib.sha256(text.encode()).hexdigest())


SAME = "sharepoint:eng/specs/radio.docx#c12@v7"


@pytest.mark.parametrize("first,second", [("R4", "R1"), ("R1", "R4")])
def test_same_chunk_keeps_most_restrictive_label(first, second):
    # second external review, B09: [same: R4] then [same: R1] returned {R1}
    best, labels = rrf([[P(SAME, [first])], [P(SAME, [second])]])
    assert best == [SAME]
    assert labels[SAME] == {"R1", "R4"}
    assert "R4" in classes_present(best, labels, [])


def test_identity_conflict_fails_closed():
    with pytest.raises(ValueError):
        rrf([[P(SAME, ["R1"], "text A")], [P(SAME, ["R1"], "text B")]])


def test_duplicate_within_one_list_gets_one_vote():
    a, b = "rack:wiki/a#c1@v1", "rack:wiki/b#c1@v1"
    best, _ = rrf([[P(a, ["R2"]), P(a, ["R2"]), P(b, ["R2"])], [P(b, ["R2"])]], k=60)
    assert best == [b, a]    # b: 1/63 + 1/61 > a: 1/61 (a's repeat adds nothing)


def test_unlabeled_in_one_tier_fails_closed_even_if_another_labels_it():
    best, labels = rrf([[P(SAME, [])], [P(SAME, ["R1"])]])
    with pytest.raises(ValueError):
        classes_present(best, labels, [])


def test_unknown_label_fails_closed():
    best, labels = rrf([[P(SAME, ["SECRET"])]])
    with pytest.raises(ValueError):
        classes_present(best, labels, ["R1"])


def test_prompt_classes_kept_and_ties_deterministic():
    a, b = "rack:x#c1@v1", "rack:y#c1@v1"
    best, labels = rrf([[P(b, ["R2"])], [P(a, ["R3"])]])
    assert best == [a, b]    # equal scores: ordered by identity
    assert classes_present(best, labels, ["R5"]) == {"R2", "R3", "R5"}


def test_empty_and_top():
    assert rrf([]) == ([], {})
    assert rrf([[]]) == ([], {})
    ids = [f"rack:d#c{i:02d}@v1" for i in range(40)]
    best, _ = rrf([[P(i, ["R1"]) for i in ids]], top=30)
    assert best == ids[:30]


# third external review, R03: a repeat within ONE list must still be checked and its labels kept;
# only its extra rank vote is suppressed. Both entry orders.
@pytest.mark.parametrize("first,second", [("R4", "R1"), ("R1", "R4")])
def test_within_list_repeat_keeps_stricter_label(first, second):
    best, labels = rrf([[P(SAME, [first]), P(SAME, [second])]])
    assert best == [SAME]
    assert labels[SAME] == {"R1", "R4"}
    assert "R4" in classes_present(best, labels, [])


@pytest.mark.parametrize("first,second", [("text A", "text B"), ("text B", "text A")])
def test_within_list_conflicting_hash_fails_closed(first, second):
    with pytest.raises(ValueError):
        rrf([[P(SAME, ["R1"], first), P(SAME, ["R1"], second)]])


@pytest.mark.parametrize("order", ["labeled_first", "unlabeled_first"])
def test_within_list_unlabeled_repeat_fails_closed(order):
    entries = [P(SAME, ["R1"]), P(SAME, [])]
    if order == "unlabeled_first":
        entries.reverse()
    best, labels = rrf([entries])
    assert best == [SAME]
    with pytest.raises(ValueError):
        classes_present(best, labels, [])


def test_within_list_repeat_still_one_vote_after_checks():
    a, b = "rack:wiki/a#c1@v1", "rack:wiki/b#c1@v1"
    best, labels = rrf([[P(a, ["R2"]), P(b, ["R2"]), P(a, ["R3"])]], k=60)
    assert best == [a, b]                 # a: 1/61 only; b: 1/62
    assert labels[a] == {"R2", "R3"}
