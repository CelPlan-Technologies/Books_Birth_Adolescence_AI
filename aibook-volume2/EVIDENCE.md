<!-- SPDX-License-Identifier: MIT -->
# Evidence for the measured figures — Volume 2

Volume 2 reports three kinds of numbers: values calculated in the workbooks, measurements made for the book, and measurements published by others. This file covers the second and third kinds named by the second external review (register item C15): Figure 20.3 and the GB10 (DGX Spark) benchmarks. For each it records what this package contains, what it does not, and where the evidence lives. The Chapter 1 experiments of Volume 1 are covered in the Volume 1 companion package.

Hashes are SHA-256 of files present when this release was prepared (26 October 2026). No hash is given for a file that was not available.

## Volume 2, Figure 20.3 and Worked Example 20.1: ANN recall against query time

**Book values.** Recall@10 against time per query for exact (flat), HNSW (M = 32), IVF-Flat (1,024 lists) and IVF-PQ (48-byte codes), with and without rescoring the top 100: 200,000 synthetic, clustered, unit-length 384-dimensional vectors, FAISS on one CPU thread, batches of 1,000 queries. Points stated in the text: HNSW 99% at 0.27 ms, exact 5.2 ms, IVF-Flat about 0.7 ms at the same recall, IVF-PQ plateau 67%, 98% with rescoring; Worked Example 20.1 adds about 25 ms for a single unbatched exact query and 67 s to build the HNSW index on two cores.

**In the repository.** Only the numbers: the ANN Measurements sheet of `workbooks/Ch20_Companion_Workbook.xlsx` holds the stated points and derives the ratios from them; it is not a record of the measurement.

**Not included.** The data generator and its seed, the benchmark script, the raw results, the CPU model, the HNSW efConstruction and the IVF nprobe values. The book text now calls these illustrative measurements on one machine with synthetic data and says the assets are planned for publication. Until they are, Figure 20.3 cannot be reproduced from this repository.

**Plausibility check (not a reproduction).** The editors rebuilt the experiment from the text with FAISS 1.15.1 on a two-core machine and several cluster structures. Magnitudes agreed (single exact query 28–36 ms; HNSW build 24–49 s; PQ-48 plateaus well below full recall and rescoring recovers most of the loss), but the recall levels, and whether HNSW or IVF is faster at high recall, depended on the unstated cluster structure. That script and its results are review material, not published here, and do not substitute for the book's run.

## Volume 2, GB10 (DGX Spark) benchmarks: Table 32.4, Figure 32.3, Worked Example 28.2

**Book values.** DGX Spark (GB10): gpt-oss-20b MXFP4 4,506 tokens/s prefill and 83 decode; gpt-oss-120b MXFP4 2,444 and 59 (pp2048 / tg32); "earlier builds gave about 50" (Section 15.3, Volume 1); used against the 55 tokens/s bandwidth ceiling of Worked Example 28.2.

**Nature.** Published third-party measurements, not runs made for the book. Table 32.4 names them as published, with their sources: llama.cpp discussion #16578 (results in `benches/dgx-spark` of the llama.cpp repository, February 2026) and LMSYS's DGX Spark review (2025), listed in the Further Reading of Chapter 32 and Appendix A of Volume 2. The other rows of Table 32.4 are likewise published results (OpenBenchmarking, llama.cpp discussion #15013, LMSYS, community tests).

**In the repository.** Nothing beyond the book's citation: no copy of the third-party results, no hashes, and no Ch32 benchmark sheet (the Ch32 workbook has Box Fit and Indexing only). The ceilings of Worked Example 28.2 are calculations and are in `workbooks/Ch28_Companion_Workbook.xlsx`.

**Not included.** A measurement on a GB10 made for the book. The book's own acceptance procedure for a Box (Section 32.7, `box/bench/ttft.py`) is the way to obtain one on a given machine.

## What "checked" means in this release

A configuration that parses, or passes `bash -n`, `docker compose config` or a schema check, is **syntax-checked**, not tested. The check suite (`.github/workflows/check.yml`) records which checks ran; `docs/deployment-prerequisites.md` lists what was not run (no image pulled, no cluster contacted, no GPU).
