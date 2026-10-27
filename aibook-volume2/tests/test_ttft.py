# SPDX-License-Identifier: MIT
# Tests of box/bench/ttft.py (Listing 32.4, Volume 2, Section 32.7) with a mocked stream; no server or GPU needed.
# Run from the repository root:  python -m pytest tests/   (needs the openai package, which ttft.py imports)
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

pytest.importorskip("openai")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "box" / "bench"))
import ttft  # noqa: E402


def chunk(content=None, reasoning=None, usage=None):
    choices = [] if content is None and reasoning is None else [NS(delta=NS(content=content, reasoning=reasoning))]
    return NS(choices=choices, usage=usage)


def client(chunks):
    return NS(chat=NS(completions=NS(create=lambda **kw: iter(chunks))))


def test_chunks_are_not_reported_as_tokens():
    # second external review, B11: two multi-token chunks and no usage gave a "token" rate from two chunks
    s = [chunk("Hello there, "), chunk("how are you?")]
    with pytest.raises(RuntimeError):
        ttft.run(client(s), "m", "p")
    r = ttft.run(client(s), "m", "p", allow_chunks=True)
    assert r["unit"] == "chunks/s" and r["completion"] == 2


def test_usage_tokens_and_reasoning_before_content():
    s = [chunk(reasoning="Think"), chunk(reasoning="ing."), chunk("Answer"), chunk(usage=NS(completion_tokens=9))]
    r = ttft.run(client(s), "m", "p")
    assert r["unit"] == "tokens/s" and r["completion"] == 9
    assert r["ttft_visible"] >= r["ttft_any"]
    assert r["e2e"] >= r["ttft_visible"]


def test_no_tokens_fails():
    with pytest.raises(RuntimeError):
        ttft.run(client([chunk(usage=NS(completion_tokens=0))]), "m", "p")


def test_p95_nearest_rank():
    assert ttft.p95([1, 2, 3]) == 3
    assert ttft.p95(list(range(1, 21))) == 19


# third external review, R07
def test_one_event_reply_has_no_decode_rate():
    s = [chunk("Hi"), chunk(usage=NS(completion_tokens=1))]
    r = ttft.run(client(s), "m", "p")
    assert r["decode"] is None and r["completion"] == 1


def test_mixed_units_are_rejected():
    res = [{"unit": "tokens/s"}, {"unit": "chunks/s"}]
    with pytest.raises(RuntimeError):
        ttft.common_unit(res)
    assert ttft.common_unit([{"unit": "tokens/s"}] * 3) == "tokens/s"


def test_main_stops_on_mixed_units(monkeypatch, capsys):
    calls = iter([[chunk("a"), chunk("b"), chunk(usage=NS(completion_tokens=2))],   # usage: tokens/s
                  [chunk("a"), chunk("b")]])                                         # none: chunks/s
    monkeypatch.setattr(ttft, "OpenAI", lambda **kw: NS(chat=NS(completions=NS(create=lambda **k: iter(next(calls))))))
    with pytest.raises(SystemExit) as e:
        ttft.main(["--model", "m", "--warmup", "0", "--runs", "2", "--allow-chunks"])
    assert e.value.code == 1
    assert "different units" in capsys.readouterr().err


@pytest.mark.parametrize("args", [["--runs", "0"], ["--runs", "-1"], ["--max-tokens", "0"], ["--warmup", "-1"],
                                  ["--runs", "x"]])
def test_main_rejects_bad_counts(args):
    with pytest.raises(SystemExit) as e:
        ttft.main(["--model", "m"] + args)
    assert e.value.code == 2


def test_run_rejects_bad_output_limit():
    with pytest.raises(ValueError):
        ttft.run(client([chunk("a")]), "m", "p", max_tokens=0)


def test_main_zero_warmup_is_accepted(monkeypatch, capsys):
    monkeypatch.setattr(ttft, "OpenAI", lambda **kw: client([chunk("a"), chunk("b"), chunk(usage=NS(completion_tokens=2))]))
    ttft.main(["--model", "m", "--warmup", "0", "--runs", "1"])
    assert "1 runs after 0 warm-up" in capsys.readouterr().out
