# SPDX-License-Identifier: MIT
"""ch01_glove_embeddings.py - companion program of Volume 1, Section 1.10.2.

Draws Figure 1.9, "A real embedding space", and prints the numbers quoted
in Section 1.10.2, from the GloVe word vectors of Pennington, Socher and
Manning (2014): the 6-billion-token release with 400,000 words and 100
dimensions.

  (a) forty words from five groups projected onto their first two
      principal components, and the share of the variance those keep;
  (b) eight words about people projected onto the man -> woman and
      man -> king directions, and the word nearest to king - man + woman;
  (c) the nearest neighbors of "king" and "piano" by cosine similarity.

The vectors: download glove.6B.zip (822 MB) from
https://nlp.stanford.edu/projects/glove/ ; the program reads the file
glove.6B.100d.txt inside it, so the zip need not be unpacked. The same
vectors are also distributed as glove-wiki-gigaword-100.gz (128 MB, with
a one-line header), which the program reads too.

    pip install numpy matplotlib
    python ch01_glove_embeddings.py glove.6B.zip
    python ch01_glove_embeddings.py glove.6B.100d.txt --out figure_1_9.png
"""
import argparse
import gzip
import io
import zipfile

import numpy as np

GROUPS = {
    'People': ['man', 'woman', 'king', 'queen', 'prince', 'princess', 'father', 'mother'],
    'Countries and capitals': ['france', 'paris', 'germany', 'berlin', 'italy', 'rome',
                               'spain', 'madrid', 'japan', 'tokyo'],
    'Food': ['bread', 'cheese', 'rice', 'sugar', 'coffee', 'wine', 'apple', 'soup'],
    'Numbers': ['one', 'two', 'three', 'four', 'five', 'six', 'ten'],
    'Music': ['piano', 'violin', 'cello', 'guitar', 'drums', 'jazz', 'orchestra'],
}
COLORS = {'People': '#B8641B', 'Countries and capitals': '#2D6A88', 'Food': '#6B8E23',
          'Numbers': '#7A5BA6', 'Music': '#A33A55'}
PEOPLE = ['king', 'queen', 'prince', 'princess', 'man', 'woman', 'boy', 'girl']
# label positions (offset in points, alignment) where words would overlap in panel (a)
LABELS = {'five': (2, 7, 'left'), 'three': (-6, 4, 'right'), 'two': (6, 2, 'left'), 'six': (6, -8, 'left'),
          'four': (-8, 14, 'right'), 'one': (0, 7, 'left'), 'ten': (0, 7, 'left'),
          'king': (8, 0, 'left'), 'father': (8, -5, 'left'), 'queen': (6, -17, 'left'),
          'mother': (8, 6, 'left'), 'princess': (-3, 7, 'right'), 'prince': (5, -4, 'left'),
          'man': (6, -2, 'left'), 'woman': (6, -2, 'left'),
          'violin': (-6, -3, 'right'), 'cello': (6, -9, 'left'), 'piano': (-4, 9, 'left'),
          'france': (-6, 6, 'left'), 'germany': (2, -11, 'center'), 'spain': (7, 0, 'left'),
          'italy': (6, 4, 'left'), 'madrid': (-4, 7, 'left'), 'paris': (6, -2, 'left'), 'rome': (6, 5, 'left'),
          'tokyo': (6, -3, 'left'), 'japan': (0, 8, 'center'), 'berlin': (6, -2, 'left'),
          'coffee': (-8, 0, 'right'), 'sugar': (-2, 7, 'right'), 'cheese': (2, 7, 'left'), 'wine': (6, 4, 'left'),
          'apple': (6, -3, 'left'), 'soup': (6, 3, 'left'), 'rice': (0, 7, 'left'), 'bread': (0, 7, 'left')}
LEADERS = {'four'}                                         # labels set apart, with a thin leader line


def open_vectors(path):
    """A text stream of the 100-dimensional vectors, from a .zip, .gz or .txt file."""
    if path.endswith('.zip'):
        z = zipfile.ZipFile(path)
        name = next(n for n in z.namelist() if n.endswith('100d.txt'))
        return io.TextIOWrapper(z.open(name), encoding='utf-8')
    if path.endswith('.gz'):
        return gzip.open(path, 'rt', encoding='utf-8')
    return open(path, encoding='utf-8')


def load(path):
    words, rows = [], []
    with open_vectors(path) as f:
        for line in f:
            parts = line.rstrip('\n').split(' ')
            if len(parts) == 2:                            # header line of the word2vec format
                continue
            words.append(parts[0])
            rows.append(np.asarray(parts[1:], dtype=np.float32))
    return words, np.vstack(rows)


def main():
    parser = argparse.ArgumentParser(description='Draws Figure 1.9 of Volume 1 from the GloVe vectors.')
    parser.add_argument('vectors', help='glove.6B.zip, glove.6B.100d.txt or glove-wiki-gigaword-100.gz')
    parser.add_argument('--out', default='figure_1_9_embedding_space.png', help='image file to write')
    args = parser.parse_args()

    words, W = load(args.vectors)
    index = {w: i for i, w in enumerate(words)}
    unit = W / np.linalg.norm(W, axis=1, keepdims=True)
    vec = lambda w: W[index[w]]
    print(f'{len(words):,} words of {W.shape[1]} dimensions')

    def neighbors(v, k, exclude):
        s = unit @ (v / np.linalg.norm(v))
        out = []
        for i in np.argsort(-s):
            if words[i] not in exclude:
                out.append((words[i], float(s[i])))
                if len(out) == k:
                    break
        return out

    # (a) principal components of the forty words
    forty = [w for g in GROUPS.values() for w in g]
    X = np.vstack([vec(w) for w in forty])
    Xc = X - X.mean(0)
    _, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    kept = (S[:2] ** 2).sum() / (S ** 2).sum()
    P = Xc @ Vt[:2].T
    i = forty.index('bread')                               # orient the axes as in the book
    P *= np.sign(P[i])
    print(f'(a) the first two principal components keep {100 * kept:.0f}% of the variance')

    # (b) the man -> woman and man -> king directions (the second made perpendicular to the first)
    e1 = vec('woman') - vec('man')
    e1 /= np.linalg.norm(e1)
    d2 = vec('king') - vec('man')
    e2 = d2 - (d2 @ e1) * e1
    e2 /= np.linalg.norm(e2)
    B = {w: ((vec(w) - vec('man')) @ e1, (vec(w) - vec('man')) @ e2) for w in PEOPLE}
    target = unit[index['king']] - unit[index['man']] + unit[index['woman']]
    best = neighbors(target, 1, {'king', 'man', 'woman'})[0]
    print(f'(b) nearest word to king - man + woman: {best[0]} (cosine {best[1]:.2f})')

    # (c) nearest neighbors in all 100 dimensions
    near = {w: neighbors(vec(w), 5, {w}) for w in ('king', 'piano')}
    for w, ns in near.items():
        print(f'(c) {w}: ' + ', '.join(f'{n} {c:.2f}' for n, c in ns))

    draw(forty, P, kept, B, best, near, args.out)
    print(f'Figure saved to {args.out}')


def draw(forty, P, kept, B, best, near, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    GOLD, FILL, DARK, GREY, RULE = '#C8941A', '#F5EDDC', '#262626', '#666666', '#E5DFD3'
    SERIF = 'DejaVu Serif'
    w, h = 2500, 1500
    fig = plt.figure(figsize=(w / 250, h / 250), dpi=250)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, w); ax.set_ylim(h, 0); ax.axis('off')
    ax.add_patch(FancyBboxPatch((8, 8), w - 16, h - 16, boxstyle='round,pad=0,rounding_size=22',
                                fc='white', ec=GOLD, lw=3.2))
    ax.add_patch(FancyBboxPatch((55, 50), 150, 62, boxstyle='round,pad=0,rounding_size=26',
                                fc=FILL, ec=GOLD, lw=2))
    ax.text(130, 81, 'Ch 1', ha='center', va='center', family=SERIF, fontsize=12, color=DARK)
    ax.text(w / 2, 78, 'A Real Embedding Space', ha='center', va='center', family=SERIF,
            fontsize=23, weight='bold', color=DARK)
    ax.text(w / 2, 145, 'Forty word vectors of 100 dimensions each, seen from three angles',
            ha='center', va='center', family=SERIF, fontsize=13.5, style='italic', color=GREY)
    ax.plot([100, w - 100], [195, 195], color=RULE, lw=1.6)
    ax.text(w / 2, 1385, 'GloVe vectors (Pennington, Socher and Manning, 2014): 400,000 words, 100 dimensions, '
            'trained on Wikipedia and Gigaword.', ha='center', family=SERIF, fontsize=8.8, style='italic', color=GREY)
    ax.text(w / 2, 1430, f'(a) principal components, keeping {100 * kept:.0f}% of the variance — 2-D distances are '
            'approximate; (b) projection on two word directions; (c) cosines in 100 dimensions.',
            ha='center', family=SERIF, fontsize=8.8, style='italic', color=GREY)

    def style(a):
        for s in ('top', 'right'):
            a.spines[s].set_visible(False)
        for s in ('left', 'bottom'):
            a.spines[s].set_color('#AAA090')
        a.tick_params(labelsize=9.5, colors=GREY)

    # (a)
    a = fig.add_axes([0.07, 0.17, 0.46, 0.62])
    k = 0
    for g, ws in GROUPS.items():
        a.scatter(P[k:k + len(ws), 0], P[k:k + len(ws), 1], s=26, color=COLORS[g], label=g, zorder=3)
        for j, word in enumerate(ws):
            dx, dy, ha = LABELS.get(word, (4, 4, 'left'))
            line = dict(arrowstyle='-', color='#B0A890', lw=0.6) if word in LEADERS else None
            a.annotate(word, (P[k + j, 0], P[k + j, 1]), xytext=(dx, dy), textcoords='offset points',
                       ha=ha, va='center', family=SERIF, fontsize=8, color=DARK, arrowprops=line)
        k += len(ws)
    style(a)
    a.set_xlabel('first principal component', family=SERIF, fontsize=9, style='italic', color=GREY)
    a.set_ylabel('second principal component', family=SERIF, fontsize=9, style='italic', color=GREY)
    a.legend(loc='lower left', frameon=False, prop={'family': SERIF, 'size': 8.5})
    fig.text(0.05, 0.825, '(a) The forty words projected from 100 to 2 dimensions', family=SERIF,
             fontsize=11.5, weight='bold', color=DARK)

    # (b)
    b = fig.add_axes([0.62, 0.50, 0.34, 0.30])
    for word, (x, y) in B.items():
        b.scatter([x], [y], s=26, color=COLORS['People'], zorder=3)
        b.annotate(word, (x, y), xytext=(5, 5), textcoords='offset points', family=SERIF, fontsize=8, color=DARK)
    wx = B['woman'][0]
    kx, ky = B['king']
    b.annotate('', xy=(wx * 0.97, 0), xytext=(0, 0), arrowprops=dict(arrowstyle='-|>', color=GREY, lw=1.4))
    b.annotate('', xy=(kx + wx * 0.97, ky), xytext=(kx, ky),
               arrowprops=dict(arrowstyle='-|>', color=GREY, lw=1.4, ls='--'))
    b.scatter([kx + wx], [ky], marker='x', s=60, color=GOLD, zorder=4)
    b.text(kx + wx, ky + 0.35, 'king − man + woman', ha='right', family=SERIF, fontsize=8,
           style='italic', color=GOLD)
    b.text(wx, 1.6, f'nearest word in 100-D to\nking − man + woman: {best[0]}\n(cosine {best[1]:.2f})',
           ha='right', va='bottom', family=SERIF, fontsize=8, style='italic', color=GOLD)
    style(b)
    b.set_xlabel('man → woman direction', family=SERIF, fontsize=9, style='italic', color=GREY)
    b.set_ylabel('man → king direction', family=SERIF, fontsize=9, style='italic', color=GREY)
    fig.text(0.60, 0.825, '(b) Directions carry relationships', family=SERIF, fontsize=11.5, weight='bold', color=DARK)

    # (c)
    fig.text(0.60, 0.385, '(c) Nearest neighbors by cosine similarity', family=SERIF, fontsize=11.5,
             weight='bold', color=DARK)
    for n, (word, ns) in enumerate(near.items()):
        c = fig.add_axes([0.67 + 0.17 * n, 0.15, 0.11, 0.17])
        names = [x for x, _ in ns][::-1]
        vals = [v for _, v in ns][::-1]
        c.barh(names, vals, color=GOLD, height=0.6)
        for y, v in enumerate(vals):
            c.text(v + 0.01, y, f'{v:.2f}', va='center', family=SERIF, fontsize=8, color=DARK)
        c.set_xlim(0, 1.05)
        c.set_title(f'“{word}”', family=SERIF, fontsize=10, color=DARK)
        style(c)
        for t in c.get_yticklabels():
            t.set_family(SERIF)
    fig.savefig(out, dpi=250)
    plt.close(fig)


if __name__ == '__main__':
    main()
