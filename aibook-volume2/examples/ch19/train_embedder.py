# Listing 19.1 — Fine-tuning an embedder (Sentence Transformers 5.4–6.1)
# From "The Birth and Adolescence of Artificial Intelligence", Volume 2, Section 19.3. Illustrative: checked against the documentation of the versions in Appendix B (Volume 2), not run end to end as one system. Test in staging before use.
# SPDX-License-Identifier: MIT
"""Fine-tune an embedder on [question, positive, negative] triples (Listing 19.1).

This is the complete version of Listing 19.1. It adds what the printed
listing leaves out: a data path on the command line, input validation, a
held-out retrieval evaluation before and after training, and a precision
chosen from the hardware.

Data: a JSON Lines file, one triple per line, either as a list
    ["question", "positive passage", "negative passage"]
or as an object
    {"anchor": "question", "positive": "...", "negative": "..."}
UTF-8, no empty fields. triples.example.jsonl beside this file is a small
synthetic fixture (20 invented triples) for a smoke test; real triples come
from Worked Example 19.2 and stay out of the public repository.

Extras (requirements/embedding-training.txt):
    pip install -r requirements/embedding-training.txt
i.e. sentence-transformers[train] (which brings datasets and accelerate) and
PyTorch. Supported accelerators: an NVIDIA GPU with BF16 (Ampere or later:
the Rack and the RTX PRO GPUs of the Box) trains the 0.6B model of the book
in BF16; an older NVIDIA GPU uses FP16; Apple MPS and the CPU use FP32. The
CPU is only for the smoke test with a tiny model:

    python examples/ch19/train_embedder.py \
        --data examples/ch19/triples.example.jsonl \
        --model sentence-transformers/all-MiniLM-L6-v2 --no-instruction \
        --epochs 1 --batch-size 8 --warmup-steps 0 --output runs/smoke

The book's run (Rack GPU, real triples):

    python examples/ch19/train_embedder.py --data triples.jsonl
"""
import argparse
import json
import random
import sys

INSTR = ("Instruct: Given a technical "
         "question, retrieve manual passages "
         "that answer it\nQuery:")
FIELDS = ("anchor", "positive", "negative")


def load_triples(path):
    """Read and validate the triples; return a list of (question, positive, negative)."""
    triples = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                sys.exit(f"{path}:{n}: not valid JSON ({e.msg})")
            if isinstance(row, dict):
                row = [row.get(k) for k in FIELDS]
            if (not isinstance(row, list) or len(row) != 3
                    or not all(isinstance(x, str) and x.strip() for x in row)):
                sys.exit(f"{path}:{n}: expected [question, positive, negative] "
                         "as three non-empty strings")
            triples.append(tuple(row))
    if not triples:
        sys.exit(f"{path}: no triples")
    return triples


def split(triples, eval_fraction, seed):
    """Hold out whole questions (all their triples) for evaluation."""
    questions = sorted({q for q, _, _ in triples})
    random.Random(seed).shuffle(questions)
    n_eval = round(len(questions) * eval_fraction)
    if eval_fraction > 0 and n_eval == 0:
        n_eval = 1
    if n_eval >= len(questions):
        sys.exit("too few distinct questions to hold any out; lower --eval-fraction")
    held = set(questions[:n_eval])
    return ([t for t in triples if t[0] not in held],
            [t for t in triples if t[0] in held])


def choose_precision(requested):
    """bf16 on GPUs that support it, fp16 on older NVIDIA GPUs, fp32 elsewhere."""
    import torch
    if requested != "auto":
        return requested
    if torch.cuda.is_available():
        return "bf16" if torch.cuda.is_bf16_supported() else "fp16"
    return "fp32"                     # CPU and Apple MPS


def make_evaluator(held_out, train, instr, name):
    """Retrieval of each held-out question's positive among all passages."""
    try:
        from sentence_transformers.sentence_transformer.evaluation import (
            InformationRetrievalEvaluator)
    except ImportError:                       # older module layout
        from sentence_transformers.evaluation import InformationRetrievalEvaluator
    passages = sorted({p for _, p, n in held_out + train for p in (p, n)})
    pid = {p: f"d{i}" for i, p in enumerate(passages)}
    qid = {}
    relevant = {}
    for q, p, _ in held_out:
        qid.setdefault(q, f"q{len(qid)}")
        relevant.setdefault(qid[q], set()).add(pid[p])
    return InformationRetrievalEvaluator(
        queries={i: q for q, i in qid.items()},
        corpus={i: p for p, i in pid.items()},
        relevant_docs=relevant, name=name, query_prompt=instr,
        mrr_at_k=[10], ndcg_at_k=[10], accuracy_at_k=[1, 5],
        precision_recall_at_k=[1, 5], map_at_k=[10],
        show_progress_bar=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", default="triples.jsonl",
                    help="JSON Lines triples (default: triples.jsonl)")
    ap.add_argument("--eval-data", help="separate held-out triples; "
                    "default: hold out --eval-fraction of the questions")
    ap.add_argument("--eval-fraction", type=float, default=0.2)
    ap.add_argument("--model", default="Qwen/Qwen3-Embedding-0.6B")
    ap.add_argument("--no-instruction", action="store_true",
                    help="do not prefix queries (for models without one)")
    ap.add_argument("--output", default="celplan-embed-v1")
    ap.add_argument("--epochs", type=float, default=3)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--mini-batch-size", type=int, default=4)
    ap.add_argument("--warmup-steps", type=int, default=200)
    ap.add_argument("--precision", choices=["auto", "bf16", "fp16", "fp32"],
                    default="auto")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    from datasets import Dataset
    from sentence_transformers import (
        SentenceTransformer,
        SentenceTransformerTrainer as Trainer,
        SentenceTransformerTrainingArguments as Args)
    from sentence_transformers.sentence_transformer import losses

    triples = load_triples(a.data)
    if a.eval_data:
        train_t, held_t = triples, load_triples(a.eval_data)
    else:
        train_t, held_t = split(triples, a.eval_fraction, a.seed)
    instr = "" if a.no_instruction else INSTR
    precision = choose_precision(a.precision)
    print(f"{len(train_t)} training and {len(held_t)} held-out triples; "
          f"precision {precision}", flush=True)

    model = SentenceTransformer(a.model)
    train = Dataset.from_dict({
        "anchor":   [instr + q for q, _, _ in train_t],
        "positive": [p for _, p, _ in train_t],
        "negative": [n for _, _, n in train_t]})
    evaluator = make_evaluator(held_t, train_t, instr, "held-out") if held_t else None
    if evaluator:
        before = evaluator(model)
    args = Args(a.output,
        num_train_epochs=a.epochs, warmup_steps=a.warmup_steps,
        per_device_train_batch_size=a.batch_size,
        bf16=precision == "bf16", fp16=precision == "fp16",
        batch_sampler="no_duplicates", seed=a.seed,
        save_strategy="no", report_to="none")
    # InfoNCE with in-batch and hard negatives over
    # the whole batch, in mini-batches of 4 texts
    loss = losses.CachedMultipleNegativesRankingLoss(
        model, mini_batch_size=a.mini_batch_size)
    Trainer(model=model, args=args,
            train_dataset=train, loss=loss).train()
    model.save(a.output)
    if evaluator:
        after = evaluator(model)
        print("held-out retrieval (before -> after training):")
        for key in sorted(after):
            if key in before and any(m in key for m in
                                     ("ndcg@10", "mrr@10", "accuracy@1", "recall@5")):
                print(f"  {key:<40} {before[key]:.3f} -> {after[key]:.3f}")
    print(f"model saved to {a.output}")


if __name__ == "__main__":
    main()
