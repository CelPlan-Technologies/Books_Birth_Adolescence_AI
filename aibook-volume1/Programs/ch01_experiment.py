# SPDX-License-Identifier: MIT
"""ch01_experiment.py - companion program of Volume 1, Section 1.11.11.

Counting models versus a small neural language model, on one documented
split of the 17-book corpus. Reproduces Table 1.10 (counting models:
training and held-out loss) and Table 1.11 (neural model: held-out loss
during training), and saves the results that ch01_experiment_figures.py
draws as Figures 1.11 and 1.12.

Corpus: the 17 Project Gutenberg books distributed with NLTK, without the
King James Bible; lowercased, every run of non-letters replaced by one
space, so that 27 symbols remain (26 letters and the space).
Split: lines shuffled with random seed 0; 90% training, 10% held-out.
Counting models: training loss = conditional entropy of the training
text, without smoothing; held-out loss with Witten-Bell interpolation
(each order backs off to the shorter contexts).
Neural model: 8 letters of context, 10-number embeddings, one tanh layer
of 384 units, softmax over 27 symbols (41,769 parameters); Adam with a
learning rate of 0.003, mini-batches of 4,096 positions, seed 0.

    pip install numpy nltk
    python ch01_experiment.py              # books downloaded by NLTK
    python ch01_experiment.py FOLDER       # or a folder with the .txt files

The whole run takes about 15 minutes and 2.5 GB of memory on a current
laptop; the results are the same on every run.
"""
import argparse
import collections
import json
import math
import os
import random
import re

import numpy as np

KMAX = 9                                   # longest context of the tables
ALPHABET = ' abcdefghijklmnopqrstuvwxyz'
V = len(ALPHABET)                          # 27 symbols


def load_books(folder=None, encoding='latin-1'):
    """The books as (name, text) pairs, from NLTK or a folder, in name order."""
    if folder:
        names = sorted(n for n in os.listdir(folder)
                       if n.endswith('.txt') and 'bible' not in n)
        books = []
        for name in names:
            with open(os.path.join(folder, name), encoding=encoding) as f:
                books.append((name, f.read()))
        return books
    import nltk
    nltk.download('gutenberg', quiet=True)
    from nltk.corpus import gutenberg
    return [(name, gutenberg.raw(name)) for name in sorted(gutenberg.fileids())
            if 'bible' not in name]


def normalize(line):
    return re.sub(r'[^a-z]+', ' ', line.lower()).strip()


def split_corpus(books):
    """Non-empty lines, shuffled with seed 0 and split 90/10.
    Each part keeps the original order of its lines."""
    lines = [s for _, text in books for s in (normalize(l) for l in text.split('\n')) if s]
    random.seed(0)
    order = list(range(len(lines)))
    random.shuffle(order)
    in_train = set(order[:int(0.9 * len(order))])
    train = ' '.join(lines[i] for i in range(len(lines)) if i in in_train)
    held = ' '.join(lines[i] for i in range(len(lines)) if i not in in_train)
    return train, held


def counting_models(train, held):
    """Table 1.10: table entries, training loss and held-out loss (bits per letter)."""
    joint, ctxc, types = [None] * (KMAX + 1), [None] * (KMAX + 1), [None] * (KMAX + 1)
    for k in range(KMAX + 1):
        j = collections.Counter(train[i - k:i + 1] for i in range(k, len(train)))
        c, t = collections.Counter(), collections.Counter()
        for g, v in j.items():
            c[g[:-1]] += v
            t[g[:-1]] += 1
        joint[k], ctxc[k], types[k] = j, c, t

    def p_wb(h, x, k):
        """Witten-Bell interpolated probability of x after the context h of length k."""
        if k == 0:
            tot = ctxc[0]['']
            lam = tot / (tot + types[0][''])
            return lam * joint[0].get(x, 0) / tot + (1 - lam) / V
        lower = p_wb(h[1:], x, k - 1)
        c = ctxc[k].get(h, 0)
        if c == 0:
            return lower
        lam = c / (c + types[k][h])
        return lam * joint[k].get(h + x, 0) / c + (1 - lam) * lower

    rows = []
    for k in range(1, KMAX + 1):
        tot = sum(joint[k].values())
        train_loss = -sum(v / tot * math.log2(v / ctxc[k][g[:-1]]) for g, v in joint[k].items())
        held_loss = -sum(math.log2(p_wb(held[i - k:i], held[i], k))
                         for i in range(KMAX, len(held))) / (len(held) - KMAX)
        rows.append({'k': k, 'entries': len(joint[k]), 'train': train_loss, 'held': held_loss})
        print(f'  {k} letters: {len(joint[k]):>9,} entries, training {train_loss:.2f}, '
              f'held-out {held_loss:.2f} bits per letter', flush=True)
    return rows


def neural_model(train, held):
    """Table 1.11: held-out loss of a small neural model during training."""
    def encode(s):
        a = np.frombuffer(s.encode('ascii'), dtype=np.uint8).copy()
        return np.where(a == 32, 0, a - 96).astype(np.int64)

    T, H = encode(train), encode(held)
    C = 8                                                  # letters of context
    rng = np.random.default_rng(0)
    E = rng.normal(0, 0.1, (V, 10))                        # embedding table
    W1 = rng.normal(0, 1 / np.sqrt(80), (80, 384)); b1 = np.zeros(384)
    W2 = rng.normal(0, 1 / np.sqrt(384), (384, V)); b2 = np.zeros(V)
    P = [E, W1, b1, W2, b2]
    print(f'  {sum(p.size for p in P):,} parameters', flush=True)
    m = [np.zeros_like(p) for p in P]
    v = [np.zeros_like(p) for p in P]
    lr, B1, B2, eps = 0.003, 0.9, 0.999, 1e-8
    window = np.arange(-C, 0)

    def forward(ix, seq):
        X = seq[ix[:, None] + window]                      # (n, 8) letter numbers
        e = E[X].reshape(len(ix), 80)
        h = np.tanh(e @ W1 + b1)
        z = h @ W2 + b2
        z -= z.max(1, keepdims=True)
        p = np.exp(z)
        p /= p.sum(1, keepdims=True)
        return X, e, h, p

    def held_loss():
        s, n = 0.0, 0
        for a in range(C, len(H), 200000):
            ix = np.arange(a, min(a + 200000, len(H)))
            _, _, _, p = forward(ix, H)
            s -= np.log(p[np.arange(len(ix)), H[ix]]).sum()
            n += len(ix)
        return s / n

    curve, step = [], 0
    for target in [0, 100, 500, 1000, 2000, 4000, 8000, 12000]:
        while step < target:
            ix = rng.integers(C, len(T), 4096)
            X, e, h, p = forward(ix, T)
            y = T[ix]
            g = p
            g[np.arange(len(ix)), y] -= 1                  # gradient p - t
            g /= len(ix)
            gW2 = h.T @ g; gb2 = g.sum(0)
            gh = (g @ W2.T) * (1 - h * h)
            gW1 = e.T @ gh; gb1 = gh.sum(0)
            ge = (gh @ W1.T).reshape(len(ix), C, 10)
            gE = np.zeros_like(E)
            np.add.at(gE, X, ge)
            step += 1
            for i, (pp, gg) in enumerate(zip(P, [gE, gW1, gb1, gW2, gb2])):   # Adam
                m[i] = B1 * m[i] + (1 - B1) * gg
                v[i] = B2 * v[i] + (1 - B2) * gg * gg
                mh = m[i] / (1 - B1 ** step)
                vh = v[i] / (1 - B2 ** step)
                pp -= lr * mh / (np.sqrt(vh) + eps)
        L = held_loss()
        curve.append({'step': target, 'nats': L, 'bits': L / math.log(2), 'ppl': math.exp(L)})
        print(f'  step {target:>6,}: {L:.2f} nats, {L / math.log(2):.2f} bits, '
              f'perplexity {math.exp(L):.1f}', flush=True)
    return curve


def main():
    parser = argparse.ArgumentParser(description='Reproduces Tables 1.10 and 1.11 of Volume 1.')
    parser.add_argument('folder', nargs='?', help='folder with the book files (default: NLTK)')
    parser.add_argument('--out', default='ch01_experiment_results.json',
                        help='results file read by ch01_experiment_figures.py')
    parser.add_argument('--encoding', default='latin-1',
                        help='encoding of the files in FOLDER (default latin-1, as the NLTK books)')
    args = parser.parse_args()

    books = load_books(args.folder, args.encoding)
    if not books:
        parser.error(f'no .txt files in {args.folder}')
    if len(books) != 17:
        print(f'Note: {len(books)} books, not the 17 of Chapter 1')
    train, held = split_corpus(books)
    if len(held) <= KMAX or len(train) <= KMAX:
        parser.error('the corpus is too short for a 90/10 split with 9 letters of context')
    results = {'train_chars': len(train), 'held_chars': len(held)}
    print(f'{len(books)} books: {len(train):,} training and {len(held):,} held-out characters')
    print('Counting models (Table 1.10)')
    results['counting'] = counting_models(train, held)
    print('Neural model (Table 1.11)')
    results['neural'] = neural_model(train, held)
    with open(args.out, 'w') as f:
        json.dump(results, f, indent=1)
    print(f'Results saved to {args.out}')


if __name__ == '__main__':
    main()
