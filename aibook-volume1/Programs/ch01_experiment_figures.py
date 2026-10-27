# SPDX-License-Identifier: MIT
"""ch01_experiment_figures.py - companion program of Volume 1, Section 1.11.11.

Draws Figure 1.11 (counting versus learning) and Figure 1.12 (what neural
models bring to counting) from the results saved by ch01_experiment.py.

    pip install matplotlib
    python ch01_experiment.py                  # writes ch01_experiment_results.json
    python ch01_experiment_figures.py          # writes the two figures as PNG files
"""
import argparse
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

GOLD, FILL, LIGHT, DARK, GREY, RULE, BLUE = '#C8941A', '#F5EDDC', '#FAF6EE', '#262626', '#666666', '#E5DFD3', '#4E6E7A'
SERIF = 'DejaVu Serif'


def frame(w, h, title, sub):
    """The frame, chapter tag, title and subtitle of the book's figures."""
    fig = plt.figure(figsize=(w / 250, h / 250), dpi=250)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, w); ax.set_ylim(h, 0); ax.axis('off')
    ax.add_patch(FancyBboxPatch((8, 8), w - 16, h - 16, boxstyle='round,pad=0,rounding_size=22', fc='white', ec=GOLD, lw=3.2))
    ax.add_patch(FancyBboxPatch((55, 62), 150, 62, boxstyle='round,pad=0,rounding_size=26', fc=FILL, ec=GOLD, lw=2))
    ax.text(130, 93, 'Ch 1', ha='center', va='center', family=SERIF, fontsize=12, color=DARK)
    ax.text(w / 2, 85, title, ha='center', va='center', family=SERIF, fontsize=23, weight='bold', color=DARK)
    ax.text(w / 2, 165, sub, ha='center', va='center', family=SERIF, fontsize=13.5, style='italic', color=GREY)
    ax.plot([100, w - 100], [220, 220], color=RULE, lw=1.6)
    return fig, ax


def figure_1_11(R, out):
    w, h = 2500, 1250
    fig, _ = frame(w, h, 'Counting Versus Learning',
                   'Training and held-out loss as the context grows (17 Gutenberg books, 90/10 split)')
    ax = fig.add_axes([0.10, 0.13, 0.85, 0.68])
    C = R['counting']
    k = [c['k'] for c in C]
    tr = [c['train'] for c in C]
    he = [c['held'] for c in C]
    ax.plot(k, tr, '-o', color=BLUE, lw=3, ms=8, label='counting model, training text')
    ax.plot(k, he, '-o', color=GOLD, lw=3, ms=8, label='counting model, held-out text (smoothed)')
    nn = [n for n in R['neural'] if n['step'] == 12000][0]['bits']
    ax.plot([8], [nn], 'D', color=DARK, ms=13, label='neural model (41,769 parameters), held-out')
    best = min(C, key=lambda c: c['held'])
    c8 = [c for c in C if c['k'] == 8][0]
    ax.text(9.15, he[-1], 'held-out', color=GOLD, family=SERIF, fontsize=13, va='center')
    ax.text(9.15, tr[-1], 'training', color=BLUE, family=SERIF, fontsize=13, va='center')
    ax.annotate(f"best counting model on unseen text\n({best['k']} letters, {best['entries']:,} entries, {best['held']:.2f} bits)",
                xy=(best['k'], best['held']), xytext=(6.2, 0.22), family=SERIF, fontsize=12,
                arrowprops=dict(arrowstyle='-', color=GREY, lw=1.2))
    ax.annotate(f"same 8-letter context:\n{c8['entries'] / 1e6:.1f} million entries → {c8['held']:.2f} bits\n"
                f"41,769 parameters → {nn:.2f} bits",
                xy=(8, nn), xytext=(6.2, 3.05), family=SERIF, fontsize=12,
                arrowprops=dict(arrowstyle='-', color=GREY, lw=1.2))
    ax.set_xlim(0.6, 9.9); ax.set_ylim(0, 3.7); ax.set_xticks(k)
    ax.set_xlabel('letters of context', family=SERIF, fontsize=14, style='italic')
    ax.set_ylabel('loss (bits per letter)', family=SERIF, fontsize=14, style='italic')
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color('#AAA090')
    ax.grid(axis='y', color='#EEE8DA', lw=1.2); ax.set_axisbelow(True)
    ax.tick_params(labelsize=13, colors=GREY)
    for t in ax.get_xticklabels() + ax.get_yticklabels():
        t.set_family(SERIF)
    ax.legend(loc='lower left', frameon=False, prop={'family': SERIF, 'size': 12})
    fig.savefig(out, dpi=250)
    plt.close(fig)


def figure_1_12(R, out):
    C = R['counting']
    c8 = [c for c in C if c['k'] == 8][0]
    nn = [n for n in R['neural'] if n['step'] == 12000][0]['bits']
    w, h = 2500, 975
    fig, ax = frame(w, h, 'What Neural Models Bring to Counting',
                    'Same training text, same 8-letter context, measured on unseen text')
    ratio = c8['entries'] / 41769
    boxes = [(125, 'Counting model (n-gram)', 'stores the combinations it has seen', f"{c8['entries'] / 1e6:.1f} million",
              c8['held'], 'table entries', 'without smoothing, unseen combinations cost ∞', LIGHT),
             (1275, 'Neural model', 'learns reusable regularities', '41,769', nn, 'parameters',
              f"{ratio:.0f}× fewer numbers, within {nn - c8['held']:.2f} bits", FILL)]
    for x, title, sub, big, bits, unit, foot, fc in boxes:
        ax.add_patch(FancyBboxPatch((x, 250), 1100, 640, boxstyle='round,pad=0,rounding_size=18', fc=fc, ec=GOLD, lw=2.6))
        ax.text(x + 550, 305, title, ha='center', va='center', family=SERIF, fontsize=16, weight='bold', color=DARK)
        ax.text(x + 550, 400, sub, ha='center', va='center', family=SERIF, fontsize=13.5, style='italic', color=GREY)
        ax.text(x + 290, 585, big, ha='center', va='center', family=SERIF, fontsize=25, weight='bold', color=DARK)
        ax.text(x + 290, 700, unit, ha='center', va='center', family=SERIF, fontsize=13, color=GREY)
        ax.text(x + 825, 585, f'{bits:.2f}', ha='center', va='center', family=SERIF, fontsize=30, weight='bold', color=GOLD)
        ax.text(x + 825, 700, 'bits per letter', ha='center', va='center', family=SERIF, fontsize=13, color=GREY)
        ax.text(x + 550, 812, foot, ha='center', va='center', family=SERIF, fontsize=12, style='italic', color=DARK)
    fig.savefig(out, dpi=250)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description='Draws Figures 1.11 and 1.12 of Volume 1.')
    parser.add_argument('results', nargs='?', default='ch01_experiment_results.json',
                        help='file written by ch01_experiment.py')
    args = parser.parse_args()
    with open(args.results) as f:
        R = json.load(f)
    figure_1_11(R, 'figure_1_11_counting_versus_learning.png')
    figure_1_12(R, 'figure_1_12_neural_versus_counting.png')
    print('Figures saved: figure_1_11_counting_versus_learning.png, figure_1_12_neural_versus_counting.png')


if __name__ == '__main__':
    main()
