# SPDX-License-Identifier: MIT
"""ch03_bpe_toy.py - companion program of Volume 1, Chapter 3 (Worked Example 3.1).

Trains a byte-pair-encoding (BPE) tokenizer on the toy corpus of Worked
Example 3.1 and prints every merge, the frequency of the merged pair and
the number of symbols left in the corpus. It then uses the learned merges
to tokenize words that never occurred in training.

Rules, as in the chapter:
  * each word is split into characters followed by an end-of-word marker "_";
  * pair counts are weighted by word frequency;
  * ties are broken alphabetically (the first pair in sorted order wins).

    python ch03_bpe_toy.py          (standard Python only, 3.8 or later)
"""
from collections import Counter

CORPUS = {"low": 5, "lower": 2, "newest": 6, "widest": 3}
N_MERGES = 8
UNSEEN = ["lowest", "newer", "wider", "slow"]


def split(word):
    return tuple(word) + ("_",)


def pair_counts(vocab):
    counts = Counter()
    for symbols, freq in vocab.items():
        for a, b in zip(symbols, symbols[1:]):
            counts[(a, b)] += freq
    return counts


def apply_merge(symbols, pair):
    out, i = [], 0
    while i < len(symbols):
        if i < len(symbols) - 1 and (symbols[i], symbols[i + 1]) == pair:
            out.append(symbols[i] + symbols[i + 1])
            i += 2
        else:
            out.append(symbols[i])
            i += 1
    return tuple(out)


def total_symbols(vocab):
    return sum(len(s) * f for s, f in vocab.items())


def train(corpus, n_merges):
    vocab = {split(w): f for w, f in corpus.items()}
    merges = []
    print(f"Start: {total_symbols(vocab)} symbols")
    for k in range(1, n_merges + 1):
        counts = pair_counts(vocab)
        best = max(counts.values())
        pair = sorted(p for p, c in counts.items() if c == best)[0]  # alphabetical tie-break
        vocab = {apply_merge(s, pair): f for s, f in vocab.items()}
        merges.append(pair)
        print(f"Merge {k}: {pair[0]} + {pair[1]} -> {pair[0] + pair[1]:<9} (pair count {best:>2}); "
              f"symbols left: {total_symbols(vocab)}")
    return merges, vocab


def tokenize(word, merges):
    symbols = split(word)
    for pair in merges:  # apply the merges in the order they were learned
        symbols = apply_merge(symbols, pair)
    return symbols


if __name__ == "__main__":
    merges, vocab = train(CORPUS, N_MERGES)
    start = sum((len(w) + 1) * f for w, f in CORPUS.items())
    print(f"\nCorpus now takes {total_symbols(vocab)} of {start} symbols "
          f"({100 * total_symbols(vocab) / start:.0f}% of its original length).")
    print("\nFinal segmentation of the training words:")
    for s, f in vocab.items():
        print(f"  {' '.join(s):<16} x{f}")
    print("\nWords never seen in training:")
    for w in UNSEEN:
        print(f"  {w:<8} -> {' | '.join(tokenize(w, merges))}")
