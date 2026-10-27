# SPDX-License-Identifier: MIT
"""ch01_corpus_statistics.py - companion program of Volume 1, Chapter 1.

Repeats Shannon's measurements on the 17-book corpus of Section 1.5.2 (the
Project Gutenberg books distributed with NLTK, without the King James
Bible) and prints the numbers of Chapter 1:

  Table 1.3   artificial English, letters (orders 0-4) and words (orders 1-3)
  Table 1.4   uncertainty of the next letter as the context grows
  Table 1.5   the words that follow "of the", and the entropy of that choice
  Figure 1.7  counts of the next word after five two-word contexts
  Table 1.7   word combinations possible and observed
  Table 1.8   the share of the letter "e" in growing samples
  Table 1.12  the words that most often follow five ordinary words

All text is lowercased and every character other than a letter is replaced
by a space, leaving 26 letters and the space, as in Shannon's experiments.
The artificial English of Table 1.3 is drawn at random, so each run (or
--seed) gives new lines with the same character as those of the book.

    pip install nltk
    python ch01_corpus_statistics.py            # books downloaded by NLTK
    python ch01_corpus_statistics.py FOLDER     # or a folder with the .txt files

Files in FOLDER are read as Latin-1 by default, as the NLTK books are, so
that the results of the book are reproduced exactly; give --encoding utf-8
for your own UTF-8 files. A corpus smaller than the samples of Table 1.8 is
measured on the samples it can supply.
"""
import argparse
import collections
import math
import os
import random
import re


def load_books(folder=None, encoding='latin-1'):
    """The books as (name, text) pairs, from NLTK or a folder, in name order."""
    if folder:
        names = sorted(n for n in os.listdir(folder)
                       if n.endswith('.txt') and not n.startswith('bible'))
        books = []
        for name in names:
            with open(os.path.join(folder, name), encoding=encoding) as f:
                books.append((name, f.read()))
        return books
    import nltk
    nltk.download('gutenberg', quiet=True)
    from nltk.corpus import gutenberg
    return [(name, gutenberg.raw(name)) for name in sorted(gutenberg.fileids())
            if not name.startswith('bible')]


def letters_only(text):
    """26 letters and the space: every run of other characters becomes one space."""
    return re.sub(r'[^a-z]+', ' ', text.lower())


def entropy(counts):
    """Entropy in bits of a distribution given as counts."""
    n = sum(counts)
    return -sum(c / n * math.log2(c / n) for c in counts if c)


def conditional_entropy(s, k):
    """Uncertainty of the next symbol given the k previous ones, in bits."""
    grams = collections.Counter(s[i:i + k + 1] for i in range(len(s) - k))
    ctx = collections.Counter()
    for g, v in grams.items():
        ctx[g[:k]] += v
    n = sum(grams.values())
    return -sum(v / n * math.log2(v / ctx[g[:k]]) for g, v in grams.items())


def generate_letters(s, order, length, rng):
    """Artificial text in which each letter depends on the order-1 letters before it."""
    if order == 0:
        return ''.join(rng.choice(' abcdefghijklmnopqrstuvwxyz') for _ in range(length))
    k = order - 1
    nxt = collections.defaultdict(collections.Counter)
    for i in range(len(s) - k):
        nxt[s[i:i + k]][s[i + k]] += 1
    start = rng.randrange(len(s) - k)
    out = s[start:start + k]
    while len(out) < length:
        c = nxt[out[len(out) - k:] if k else '']
        if not c:                                       # dead end: restart from a random context
            start = rng.randrange(len(s) - k)
            out += s[start:start + k] if k else ''
            continue
        out += rng.choices(list(c), weights=list(c.values()))[0]
    return out[:length].strip()


def generate_words(words, order, length, rng):
    """Artificial text in which each word depends on the order-1 words before it."""
    k = order - 1
    nxt = collections.defaultdict(collections.Counter)
    for i in range(len(words) - k):
        nxt[tuple(words[i:i + k])][words[i + k]] += 1
    start = rng.randrange(len(words) - k)
    out = list(words[start:start + k])
    while len(out) < length:
        c = nxt[tuple(out[len(out) - k:]) if k else ()]
        if not c:
            start = rng.randrange(len(words) - k)
            out += words[start:start + k]
            continue
        out.append(rng.choices(list(c), weights=list(c.values()))[0])
    return ' '.join(out[:length])


def main():
    parser = argparse.ArgumentParser(description='Prints the corpus measurements of Chapter 1 of Volume 1.')
    parser.add_argument('folder', nargs='?', help='folder with the book files (default: NLTK)')
    parser.add_argument('--seed', type=int, default=1, help='random seed for the artificial English')
    parser.add_argument('--encoding', default='latin-1',
                        help='encoding of the files in FOLDER (default latin-1, as the NLTK books; '
                             'utf-8 for most new files)')
    args = parser.parse_args()

    books = load_books(args.folder, args.encoding)
    if not books:
        parser.error(f'no .txt files in {args.folder}')
    raw = ''.join(text + '\n' for _, text in books)
    s = letters_only(raw).strip()                       # one long string of letters and single spaces
    s = re.sub(' +', ' ', s)
    words = s.split(' ')
    if len(words) < 10 or len(s) < 100:
        parser.error(f'the corpus has {len(s)} letters and spaces and {len(words) if s else 0} words; '
                     'at least 100 and 10 are needed')
    print(f'{len(books)} books: {len(raw):,} characters, {len(words):,} words '
          f'({len(set(words)):,} distinct)\n')

    print('Table 1.3 - Artificial English (random; a new draw with each --seed)')
    rng = random.Random(args.seed)
    for order, name in [(0, 'Zero order (letters equally likely)'), (1, 'First order (letter frequencies)'),
                        (2, 'Second order (one previous letter)'), (3, 'Third order (two previous letters)'),
                        (4, 'Fourth order (three previous letters)')]:
        print(f'  {name}\n    {generate_letters(s, order, 80, rng)}')
    for order, name in [(1, 'First order, words (word frequencies)'), (2, 'Second order, words (one previous word)'),
                        (3, 'Third order, words (two previous words)')]:
        print(f'  {name}\n    {generate_words(words, order, 18, rng)}')

    print('\nTable 1.4 - Uncertainty of the next letter as context grows')
    print(f'  {"Letters of context":<36}{"bits per letter":>16}{"perplexity":>12}')
    h = math.log2(27)
    print(f'  {"None (27 symbols equally likely)":<36}{h:>16.2f}{2 ** h:>12.1f}')
    h = entropy(collections.Counter(s).values())
    print(f'  {"None (actual letter frequencies)":<36}{h:>16.2f}{2 ** h:>12.1f}')
    for k in range(1, 6):
        h = conditional_entropy(s, k)
        print(f'  {k:<36}{h:>16.2f}{2 ** h:>12.1f}')

    pairs = collections.Counter(zip(words, words[1:]))
    triples = collections.Counter(zip(words, words[1:], words[2:]))

    after = collections.Counter({c: n for (a, b, c), n in triples.items() if (a, b) == ('of', 'the')})
    total = pairs[('of', 'the')]
    h = entropy(after.values())
    print(f'\nTable 1.5 - Words following "of the": {total:,} occurrences, {len(after):,} different words; '
          f'entropy {h:.1f} bits, perplexity about {2 ** h:,.0f}')
    for w, n in after.most_common(10):
        print(f'  {w:<10}{n:>6}{100 * n / total:>7.1f}%')

    print('\nFigure 1.7 - Count of the next word after five two-word contexts')
    cols = ['world', 'whale', 'sea', 'man', 'the']
    print(f'  {"":<12}' + ''.join(f'{c:>8}' for c in cols))
    for ctx in [('of', 'the'), ('the', 'white'), ('the', 'old'), ('sat', 'on'), ('the', 'cat')]:
        print(f'  {" ".join(ctx):<12}' + ''.join(f'{triples[ctx + (c,)]:>8}' for c in cols))

    v = len(set(words))
    print('\nTable 1.7 - Word combinations possible and observed')
    for name, possible, seen in [('Single words', v, v), ('Pairs of words', v ** 2, len(pairs)),
                                 ('Triples of words', v ** 3, len(triples))]:
        print(f'  {name:<18}{possible:>22,}{seen:>12,}{100 * seen / possible:>14.6f}%')
    once = sum(1 for n in pairs.values() if n == 1) / len(pairs)
    twice = sum(1 for n in pairs.values() if n <= 2) / len(pairs)
    print(f'  Of the pairs observed, {100 * once:.0f}% occur once and {100 * twice:.0f}% at most twice.')

    print('\nTable 1.8 - Share of the letter "e" as the sample grows')
    letters = s.replace(' ', '')
    sizes = [n for n in [10, 100, 1000, 10000, 100000, 1000000] if n < len(letters)]
    for n in sizes + [len(letters)]:                    # only samples the corpus can supply
        print(f'  {n:>12,} letters: {100 * letters[:n].count("e") / n:5.1f}%')

    print('\nTable 1.12 - What word counts "know"')
    nxt = collections.defaultdict(collections.Counter)
    for (a, b), n in pairs.items():
        nxt[a][b] += n
    for w in ['captain', 'mr', 'miss', 'white', 'sperm']:
        total = sum(1 for x in words[:-1] if x == w)
        if not total:
            print(f'  {w:<8} (0): not in the corpus')
            continue
        top = ', '.join(f'{b} ({100 * n / total:.0f}%)' for b, n in nxt[w].most_common(5))
        print(f'  {w:<8} ({total:,}): {top}')


if __name__ == '__main__':
    main()
