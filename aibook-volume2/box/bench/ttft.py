# SPDX-License-Identifier: MIT
# Listing 32.4 — Measuring TTFT and decode speed
# From "The Birth and Adolescence of Artificial Intelligence", Volume 2, Section 32.7. Illustrative: checked against the documentation of the versions in Appendix B (Volume 2), not run end to end as one system. Test in staging before use.
# This file is the complete version of the printed listing: the same measurement, plus a command line, an output
# limit, warm-up calls and repeated runs reported as median and 95th percentile (5th for the decode rate).
#
# What it measures, for ONE request at a time through an OpenAI-compatible endpoint (Ollama, llama.cpp, vLLM):
#   ttft_any      time to the first generated token, reasoning or visible (a thinking model reasons first)
#   ttft_visible  time to the first token of the visible answer (content)
#   decode        tokens per second between the first and the last generated token, from the server's own token
#                 count (usage.completion_tokens, which includes reasoning tokens); the times are taken when each
#                 chunk arrives, so the final usage chunk does not lengthen the decode window
#   e2e           time to the last generated token
# If the server reports no usage, the decode rate is NOT a token rate: with --allow-chunks it is reported as
# chunks/s (a chunk may carry several tokens); without it the run stops. Runs are summarized in one unit only: if
# some runs give tokens/s and others chunks/s, the program stops instead of mixing them.
# This is a single-user latency check for the acceptance test of Section 32.7. It is not a load test: the capacity
# of a server is its goodput (Volume 1, Section 16.6), measured with many concurrent requests against a latency target.
#
# Example:  python ttft.py --model gpt-oss:20b --prompt-file rag_prompt.txt --runs 10
import argparse
import math
import os
import statistics
import time

from openai import OpenAI


def run(c, model, prompt, max_tokens=256, allow_chunks=False):
    if not isinstance(max_tokens, int) or max_tokens < 1:
        raise ValueError("max_tokens must be a positive integer")
    t0 = time.perf_counter()
    first_any = first_vis = last = use = None
    chunks = 0
    s = c.chat.completions.create(
        model=model, stream=True, max_tokens=max_tokens,
        stream_options={"include_usage": True},
        messages=[{"role": "user", "content": prompt}])
    for ch in s:
        if getattr(ch, "usage", None):
            use = ch.usage                     # the server's token count
        if not ch.choices:
            continue
        d = ch.choices[0].delta
        r = (getattr(d, "reasoning", None) or
             getattr(d, "reasoning_content", None))
        now = time.perf_counter()
        if r or d.content:
            first_any = first_any or now
            last = now
            chunks += 1
        if d.content:
            first_vis = first_vis or now
    if first_any is None:
        raise RuntimeError("no tokens received")
    if use is not None and use.completion_tokens:
        n, unit = use.completion_tokens, "tokens/s"
    elif allow_chunks:
        n, unit = chunks, "chunks/s"
    else:
        raise RuntimeError("the server reported no token usage; rerun with --allow-chunks to report chunks/s")
    span = last - first_any
    return {
        "ttft_any": first_any - t0,
        "ttft_visible": None if first_vis is None else first_vis - t0,
        "decode": (n - 1) / span if n > 1 and span > 0 else None,
        "e2e": last - t0,
        "unit": unit,
        "completion": n,
    }


def common_unit(res):
    """The one unit of all runs; mixed tokens/s and chunks/s cannot be summarized together."""
    units = sorted({r["unit"] for r in res})
    if len(units) != 1:
        raise RuntimeError(f"runs reported different units ({', '.join(units) or 'none'}); "
                           "the server gave usage for some calls only, so the rates cannot be combined")
    return units[0]


def _count(minimum):
    def parse(text):
        try:
            v = int(text)
        except ValueError:
            raise argparse.ArgumentTypeError(f"not an integer: {text!r}")
        if v < minimum:
            raise argparse.ArgumentTypeError(f"must be at least {minimum}: {v}")
        return v
    return parse


def pct(xs, q):
    """Nearest-rank percentile q (0-100) of xs."""
    s = sorted(xs)
    return s[max(0, math.ceil(q / 100 * len(s)) - 1)]


def p95(xs):
    """95th percentile of times; with fewer than 20 runs it is the slowest run."""
    return pct(xs, 95)


def main(argv=None):
    a = argparse.ArgumentParser(description="Single-request TTFT and decode speed (not a goodput load test).")
    a.add_argument("--base-url", default="http://127.0.0.1:11434/v1")
    a.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY", "local"))
    a.add_argument("--model", required=True)
    g = a.add_mutually_exclusive_group()
    g.add_argument("--prompt", default="Explain in three sentences what a KV cache is.")
    g.add_argument("--prompt-file", help="e.g. the largest RAG prompt the pipeline produces")
    a.add_argument("--max-tokens", type=_count(1), default=256, help="output limit per call (at least 1)")
    a.add_argument("--warmup", type=_count(0), default=1, help="untimed calls first (model load, caches); 0 or more")
    a.add_argument("--runs", type=_count(1), default=10, help="timed calls (at least 1)")
    a.add_argument("--allow-chunks", action="store_true", help="report chunks/s if the server gives no usage")
    o = a.parse_args(argv)
    prompt = open(o.prompt_file, encoding="utf-8").read() if o.prompt_file else o.prompt
    c = OpenAI(base_url=o.base_url, api_key=o.api_key)
    for _ in range(o.warmup):
        run(c, o.model, prompt, o.max_tokens, o.allow_chunks)
    res = [run(c, o.model, prompt, o.max_tokens, o.allow_chunks) for _ in range(o.runs)]
    try:
        unit = common_unit(res)
    except RuntimeError as e:
        a.exit(1, f"ttft: {e}\n")
    print(f"{o.model}: {o.runs} runs after {o.warmup} warm-up, max_tokens={o.max_tokens}, one request at a time")
    for key, label in (("ttft_any", "TTFT, first token (s)"), ("ttft_visible", "TTFT, first visible token (s)"),
                       ("e2e", "last token (s)"), ("decode", f"decode ({unit})")):
        xs = [r[key] for r in res if r[key] is not None]
        if xs and key == "decode":   # for a rate the bad tail is the low one
            print(f"  {label:32s} median {statistics.median(xs):8.3f}   p5  {pct(xs, 5):8.3f}   n={len(xs)}")
        elif xs:
            print(f"  {label:32s} median {statistics.median(xs):8.3f}   p95 {p95(xs):8.3f}   n={len(xs)}")
        else:
            print(f"  {label:32s} not observed")
    print("  single-user latency only; not a goodput load test")


if __name__ == "__main__":
    main()
