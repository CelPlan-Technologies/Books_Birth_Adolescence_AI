<!-- SPDX-License-Identifier: MIT -->
# The Birth and Adolescence of Artificial Intelligence — Volume 1 companion files

Companion files for **Volume 1: How Language Models Learn and Represent Human Knowledge**, by **Leonhard Korowajczuk**, first edition (October 2026). The companion files of Volume 2 (LLM System Architectures and Implementation) are distributed separately.

Release **ed1**, published with this edition at GitHub: XXX. It holds the chapter workbooks, the programs of Chapter 1, Chapter 3 and Appendix D, and the code samples printed in Volume 1.

## Layout

```
aibook-volume1/
├── README.md         this file
├── LICENSE.txt       MIT License (every file)
├── ERRATA.md         corrections, newest first
├── EVIDENCE.md       where the evidence for the Chapter 1 measurements lives
├── .env.example      template of the variables the Chapter 16 examples read
├── Workbooks/        Ch01–Ch16, AppA, AppB
├── Programs/         Python programs of Chapters 1 and 3 and Appendix D; expected/ outputs
├── examples/         code samples of Chapters 3, 6 and 16
├── docs/             credentials.md (the Chapter 16 key variables)
├── requirements/     demo.txt (pinned versions), check.txt (tests)
├── tests/            regression tests (pytest)
└── .github/          workflows/check.yml (the check suite)
```

## Workbooks (folder `Workbooks`)

One workbook per chapter of Volume 1 and for Appendices A and B. Each opens with a README sheet that lists its sheets and the sections, tables and worked examples they reproduce; the text names the sheet beside each worked example. Blue cells on a light yellow background are inputs: change them and every result recalculates. No macros and no links to other files: they open in Microsoft Excel, LibreOffice Calc and Google Sheets.

| Workbook | Chapter | Sheets |
|---|---|---|
| Ch01_Companion_Workbook.xlsx | Chapter 1 — The Birth of the Large Language Model | Entropy, Law of Large Numbers, Cosine Similarity, Attention, Loss & Gradient, Perplexity, Temperature, Corpus Experiments, Training Time, Model Memory |
| Ch02_Companion_Workbook.xlsx | Chapter 2 — Neural Network Essentials for LLMs | Neuron & Activations, Gradient Step, Number Formats, Tensor Shapes, Parameter Count, Memory, Arithmetic Intensity |
| Ch03_Companion_Workbook.xlsx | Chapter 3 — Tokenization and Embeddings | Softmax, Vocabulary Parameters, Tokenizer Tax, Chunking, Media Tokens |
| Ch04_Companion_Workbook.xlsx | Chapter 4 — The Transformer | Attention by Hand, Scaling, RoPE, Attention Cost, KV Cache, Forward Pass |
| Ch05_Companion_Workbook.xlsx | Chapter 5 — Encoder, Decoder, Encoder–Decoder: The Three Families | Objectives, Encoder Parameters, Encoder–Decoder Cost, Box Throughput |
| Ch06_Companion_Workbook.xlsx | Chapter 6 — Anatomy of a Modern Decoder-Only LLM | Config to Parameters, RMSNorm and SwiGLU, KV Designs, RoPE Wavelengths, Online Softmax, Box Budget |
| Ch07_Companion_Workbook.xlsx | Chapter 7 — Mixture of Experts | Router, Load Balance, MoE Parameters, Box Speed, Batch Coverage, Expert Traffic |
| Ch08_Companion_Workbook.xlsx | Chapter 8 — Beyond Attention: State-Space Models, Hybrids and Alternatives | Linear Attention, Selective SSM, State versus Cache, Diffusion Timing |
| Ch09_Companion_Workbook.xlsx | Chapter 9 — Multimodal Architectures | Image Tokens, Page Images, Video, Audio Tokens |
| Ch10_Companion_Workbook.xlsx | Chapter 10 — Pretraining at Scale | Corpus Size, Scaling Laws, Sharding, Pipeline Bubble, Training Cost |
| Ch11_Companion_Workbook.xlsx | Chapter 11 — Post-Training, Alignment and Reasoning | Preference Losses, GRPO Advantages, Majority Voting |
| Ch12_Companion_Workbook.xlsx | Chapter 12 — Adaptation: Fine-Tuning, LoRA and Distillation | LoRA by Hand, LoRA Parameters, Distillation, Task Arithmetic, Fine-Tune Plan |
| Ch13_Companion_Workbook.xlsx | Chapter 13 — Inference Mechanics | Latency, KV Budget, Sampling, Speculative, Batching |
| Ch14_Companion_Workbook.xlsx | Chapter 14 — Quantization and Compression | Block Quantization, Sizing, Evaluation |
| Ch15_Companion_Workbook.xlsx | Chapter 15 — Hardware for LLMs | Roofline, Devices, Rack Sizing, Power |
| Ch16_Companion_Workbook.xlsx | Chapter 16 — Serving Engines and Runtimes | GPU Memory, Multi-LoRA, Little's Law, Load Test |
| AppA_Companion_Workbook.xlsx | Appendix A — Mathematical Refresher | Vectors, Log Space, Information, Softmax, Rotation, BF16 |
| AppB_Companion_Workbook.xlsx | Appendix B — Information Theory: Shannon's Foundations | Entropy, Cross-Entropy and KL, Compression, Channel Capacity |

## Programs (folder `Programs`; Python 3.10 or later)

Install the libraries once: `pip install -r Programs/requirements.txt` (the lower bounds printed in Volume 1), or the exact tested versions with `pip install -r requirements/demo.txt`. The Chapter 1 programs use the 17 Project Gutenberg books distributed with NLTK, which NLTK downloads on the first run; Appendix D (Section D.3) covers proxies and computers without Internet access. The Chapter 1 programs list their options with `--help`. With a folder of your own `.txt` files, give `--encoding utf-8`; the default, Latin-1, reproduces the book's corpus exactly.

| Program | Purpose | Where in the book |
|---|---|---|
| `ch01_bpe_tokenizers.py` | BPE tokenizers trained on the 17-book corpus (Table 1.6) | Section 1.8.1; Appendix D |
| `ch01_corpus_statistics.py` | Shannon's measurements on the corpus (Tables 1.3–1.5, 1.7, 1.8, 1.12 and the counts of Figure 1.7) | Chapter 1 |
| `ch01_glove_embeddings.py` | Figure 1.9 and its numbers, from the GloVe vectors (glove.6B.zip, 822 MB, https://nlp.stanford.edu/projects/glove/) | Section 1.10.2 |
| `ch01_experiment.py` | Counting models against a small neural model (Tables 1.10 and 1.11); about 15 minutes and 2.5 GB of memory | Section 1.11.11 |
| `ch01_experiment_figures.py` | Figures 1.11 and 1.12, from the results of `ch01_experiment.py` | Section 1.11.11 |
| `ch03_bpe_toy.py` | A tiny BPE tokenizer in standard Python, no libraries | Worked Example 3.1 |
| `expected/` | Outputs behind the Chapter 1 tables, compared byte for byte by the tests (see `EVIDENCE.md`) | Chapter 1 |

## Code samples (folder `examples`)

| File | Content | Where in the book |
|---|---|---|
| `examples/ch03/tokenize.py` | How a tokenizer splits a Python function | Section 3.3 |
| `examples/ch06/config.json` | config.json of Qwen3-8B (Listing 6.1; abridged and reordered, values as published) | Section 6.8 |
| `examples/ch16/chat.sh` | Chat request to vLLM on the Rack (curl; requires `LLM_KEY`) | Section 16.4 |
| `examples/ch16/three_tiers.py` | One client library, three tiers (Python) | Section 16.4 |
| `examples/ch16/vllm-docker.sh` | Launching vLLM in a container on one node (requires `VLLM_API_KEY`; port on 127.0.0.1 unless `VLLM_BIND` is set) | Section 16.5 |

The code samples are illustrative: each was checked against the documentation of the software versions named in the book, but not run against live servers. Test them before use. The variables they read are explained in `docs/credentials.md`; `.env.example` is the template. JSON allows no comments, so the note on `examples/ch06/config.json` is here.

## Tests

- `pip install -r requirements/check.txt && python -m pytest tests/` runs the checks: parsing of every Python, JSON and shell file, the SPDX lines and `.gitignore` rules (`tests/test_repo_files.py`), and the Chapter 1 statistics on small synthetic corpora (`tests/test_corpus_statistics.py`). No network is needed.
- One test skips by design: the full-corpus comparison of Chapter 1. Set `NLTK_GUTENBERG_DIR` to the folder of the NLTK Gutenberg `.txt` files to run it; `pytest -rs` lists the skip and its reason.
- `.github/workflows/check.yml` runs the same checks on GitHub, plus a secret scan, and a second job that downloads the corpus, checks its hash against `EVIDENCE.md` and runs the full-corpus comparison.
- Local run, 27 October 2026 (Python 3.13, temporary Git copy): 23 pytest tests passed and 1 skipped (the full-corpus comparison), and the secret scan passed. The full-corpus comparison was last run on 26 October 2026, before the split, against the corpus whose hash is in `EVIDENCE.md`; the program and expected outputs have not changed since. The workflow itself has not yet run on GitHub.

## Errata and contact

Report errors, or statements overtaken by events, through the issue tracker of this repository (GitHub: XXX). Corrections are listed in [`ERRATA.md`](ERRATA.md) and incorporated into later editions.

## License

MIT License for every file, workbooks included; see [`LICENSE.txt`](LICENSE.txt). The text and figures of the book are not covered by this license.

© 2026 Leonhard Korowajczuk.
