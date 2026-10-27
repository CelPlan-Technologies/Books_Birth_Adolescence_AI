# SPDX-License-Identifier: MIT
"""ch01_bpe_tokenizers.py - companion program of Volume 1, Appendix D.

Trains byte-level BPE tokenizers, as in GPT-2, on the 17-book corpus
(the Project Gutenberg books distributed with NLTK, without the King
James Bible) and prints how each one splits a few words and how many
tokens per word the whole corpus needs: Table 1.6 of Section 1.8.1.

    pip install tokenizers nltk
    python ch01_bpe_tokenizers.py           # books downloaded by NLTK
    python ch01_bpe_tokenizers.py FOLDER    # or a folder of .txt files
"""
import argparse
import os
import re
import tempfile

from tokenizers import ByteLevelBPETokenizer

WORDS = ['the', 'whale', 'captain', 'happiness', 'unhappiness',
         'unbelievable', 'transformer', 'carburetor', 'Shannon', '1948']


def load_corpus(folder=None, encoding='latin-1'):
    """Return the books as (name, text) pairs, from NLTK or a folder."""
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
    return [(name, gutenberg.raw(name))
            for name in sorted(gutenberg.fileids())
            if not name.startswith('bible')]


def train(paths, vocab_size):
    """Train a byte-level BPE tokenizer on the text files in paths."""
    tokenizer = ByteLevelBPETokenizer()
    tokenizer.train(paths, vocab_size=vocab_size, min_frequency=2,
                    show_progress=False, special_tokens=[])
    return tokenizer


def pieces(tokenizer, text):
    """The tokens of text joined by '·'. Byte-level BPE keeps the space
    before a word inside the word's first token, where it is stored as
    'Ġ'; it is shown here as '_'."""
    tokens = tokenizer.encode(text).tokens
    return '·'.join(t.replace('Ġ', '_') for t in tokens)


def split(tokenizer, word):
    """How a word is split inside running text, as in Table 1.6."""
    shown = pieces(tokenizer, ' ' + word)
    return shown[1:].lstrip('·')          # drop the leading space


def running_text(text):
    """Every run of spaces and line breaks reduced to one space."""
    return re.sub(r'\s+', ' ', text).strip()


def tokens_per_word(tokenizer, text):
    """Tokens (punctuation included) per word separated by spaces."""
    words = len(text.split(' '))
    return len(tokenizer.encode(text).tokens) / words, words


def main():
    parser = argparse.ArgumentParser(
        description='Reproduces Table 1.6 of Volume 1 (Appendix D).')
    parser.add_argument('folder', nargs='?',
                        help='folder with the book files (default: NLTK)')
    parser.add_argument('--vocab', type=int, nargs='+',
                        default=[1000, 8000, 32000],
                        help='vocabulary sizes to train')
    parser.add_argument('--words', nargs='+', default=WORDS,
                        help='words whose splits are shown')
    parser.add_argument('--sentence', help='a sentence to tokenize')
    parser.add_argument('--text', help='a UTF-8 text file to measure')
    parser.add_argument('--save', help='folder for the trained tokenizers')
    parser.add_argument('--encoding', default='latin-1',
                        help='encoding of the files in FOLDER (default latin-1, as the NLTK books)')
    args = parser.parse_args()

    books = load_corpus(args.folder, args.encoding)
    if not books:
        parser.error(f'no .txt files in {args.folder}')
    if len(books) != 17:
        print(f'Note: {len(books)} books, not the 17 of Table 1.6')
    corpus = running_text('\n'.join(text for _, text in books))
    if not corpus:
        parser.error('the corpus is empty')
    with tempfile.TemporaryDirectory() as folder:   # the trainer reads files
        paths = []
        for name, text in books:
            paths.append(os.path.join(folder, name))
            with open(paths[-1], 'w', encoding='utf-8') as f:
                f.write(text)
        run(args, books, paths, corpus)


def run(args, books, paths, corpus):
    """Train one tokenizer per vocabulary size and print its splits."""
    other = None
    if args.text:
        with open(args.text, encoding='utf-8', errors='replace') as f:
            other = running_text(f.read())
    print(f'{len(books)} books, {len(corpus.split(" ")):,} words')

    for size in args.vocab:
        tokenizer = train(paths, size)
        ratio, _ = tokens_per_word(tokenizer, corpus)
        print(f'\nVocabulary of {size:,} tokens: '
              f'{ratio:.2f} tokens per word')
        for word in args.words:
            print(f'  {word:<14} {split(tokenizer, word)}')
        if args.sentence:
            print(f'  Sentence:      {pieces(tokenizer, args.sentence)}')
        if other:
            ratio, words = tokens_per_word(tokenizer, other)
            print(f'  {os.path.basename(args.text)}: {ratio:.2f} tokens '
                  f'per word ({words:,} words)')
        if args.save:
            target = os.path.join(args.save, f'bpe_{size}')
            os.makedirs(target, exist_ok=True)
            tokenizer.save_model(target)  # vocab.json and merges.txt


if __name__ == '__main__':
    main()
