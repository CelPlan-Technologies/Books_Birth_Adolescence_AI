<!-- SPDX-License-Identifier: MIT -->
# Evidence for the measured figures — Volume 1

Volume 1 reports two kinds of numbers: values calculated in the workbooks and measurements made for the book. This file covers the second kind, the Chapter 1 experiments (register item C15). For each it records what this package contains, what it does not, and where the evidence lives.

Hashes are SHA-256 of files present when this release was prepared (26 October 2026). No hash is given for a file that was not available.

## Volume 1, Chapter 1: corpus measurements and the counting-versus-neural experiment

**Book values.** Tables 1.3–1.5, 1.7, 1.8 and 1.12 and the counts of Figure 1.7 (corpus statistics); Table 1.6 (BPE tokenizers); Tables 1.10 and 1.11 and Figures 1.11 and 1.12 (Section 1.11.11 experiment). Table numbers as in `README.md`.

**Data.** The 17 Project Gutenberg books distributed with NLTK (`gutenberg` corpus), without the King James Bible. Not stored here: NLTK downloads it on the first run (`nltk.download('gutenberg')`); the books are in the public domain in the United States, and the NLTK data package carries its own terms. The copy used to verify this release:

| File | SHA-256 | Check |
|---|---|---|
| `gutenberg.zip` (NLTK data package, 4,251,829 bytes; 18 `.txt` files including `bible-kjv.txt`) | `2d3c3ab548c653944310f37f536443ec85d0a0ad855fcae217a0c9efdce2d611` | Gives the 6,339,056 training and 707,073 held-out characters recorded in the experiment's results |

NLTK does not version its data packages; if a later download has a different hash, the counts below may change.

**Programs and expected outputs** (in `Programs`):

| Program | Expected output in `Programs/expected/` | SHA-256 of the expected output | How it was obtained |
|---|---|---|---|
| `ch01_corpus_statistics.py` (default seed 1) | `ch01_corpus_statistics_seed1.txt` | `508cf5fd3f668a61a66c25b2977200c66eb2403922ba15aea8d17f7347eafa2e` | Run for this release on the folder above, before and after the C17 changes: byte-identical output. Agrees with Tables 1.4, 1.7, 1.8 and 1.12 of the book (for example 36,182 distinct words; "e" 12.4% of 5,701,893 letters). Table 1.3's artificial English is random by design |
| `ch01_bpe_tokenizers.py` | `ch01_bpe_tokenizers.txt` | `6c00bdb2492f06e69c593ea64da22a07024e334841ed1659f62ca1e20d179c82` | Run for this release (tokenizers 0.23.3), before and after the C17 changes: identical. The splits agree with Table 1.6 |
| `ch01_experiment.py` | `ch01_experiment_results.json` | `74ee4a8414d6723c8a098f6aaf55347f15b3d7fc95bd266dd702d3380d5f5395` | The results file from which the book's Tables 1.10 and 1.11 and Figures 1.11 and 1.12 were made (10 October 2026), produced by the working version of the program that preceded `ch01_experiment.py`; the computation is the same, the repository version adds the command line and comments. Rerun for this release with the repository version (after the C17 changes; Python 3.13, NumPy 2.5.3, two CPU cores, about 25 minutes): the results file was identical in every value, counting and neural |
| `ch01_experiment_figures.py` | — | — | Run for this release on `expected/ch01_experiment_results.json` (matplotlib 3.11.2); draws both figures |

Tolerances: the corpus statistics and BPE outputs are deterministic and should match exactly on the same corpus. The experiment's counting-model losses are exact sums; the neural-model losses depend on floating-point summation order (NumPy build, BLAS library, CPU), so compare them to two decimals, the precision printed in Table 1.11. The environment of the book's run was not recorded beyond Python 3 and NumPy 2.

**Not included.** GloVe (Figure 1.9, `ch01_glove_embeddings.py`): the 822 MB `glove.6B.zip` from Stanford NLP is not redistributed and was not available to compute a hash; no expected output is stored. Tokenizer training artifacts (vocabularies and merges) are not stored; `ch01_bpe_tokenizers.py --save FOLDER` regenerates them.

Reproduce:

```bash
pip install -r requirements/demo.txt
cd Programs
python ch01_corpus_statistics.py > stats.txt     # compare with expected/ch01_corpus_statistics_seed1.txt
python ch01_bpe_tokenizers.py > bpe.txt          # compare with expected/ch01_bpe_tokenizers.txt
python ch01_experiment.py                        # about 15 minutes; compare with expected/ch01_experiment_results.json
python ch01_experiment_figures.py
```

With the NLTK books unpacked in a folder, `NLTK_GUTENBERG_DIR=folder python -m pytest tests/test_corpus_statistics.py` makes the first comparison automatically.

## What "checked" means in this release

A file that parses, or passes `bash -n`, is **syntax-checked**, not tested. The check suite (`.github/workflows/check.yml`) records which checks ran. The Chapter 16 examples were not run against servers.
