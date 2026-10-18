"""Retrieval evaluation: BM25 vs dense vs hybrid vs reranked, on BEIR SciFact.

Builds each retriever over the same corpus, runs the labelled test queries, and
reports nDCG@10, Recall@10, Recall@100 and MRR@10 - computed here in plain
Python so you can see exactly what each metric does. Optional: int8 and binary
embedding quantization with float32 rescoring.

SciFact: 5,183 scientific abstracts, 300 test claims with relevance labels.
Everything runs on a laptop CPU in a few minutes.

Usage:
  python retrieval_lab.py                          # all systems
  python retrieval_lab.py --quantization           # + int8 / binary embeddings
  python retrieval_lab.py --splade                 # + learned sparse retrieval (SPLADE)
  python retrieval_lab.py --embed-model BAAI/bge-small-en-v1.5 --limit 100
"""

import argparse
import math
import time
from collections import defaultdict

import bm25s
import numpy as np
from datasets import load_dataset
from sentence_transformers import CrossEncoder, SentenceTransformer


# ---------------------------------------------------------------- data
def load_scifact():
    corpus = load_dataset("BeIR/scifact", "corpus", split="corpus")
    queries = load_dataset("BeIR/scifact", "queries", split="queries")
    qrels_rows = load_dataset("BeIR/scifact-qrels", split="test")
    doc_ids = [str(d["_id"]) for d in corpus]
    docs = [f'{d["title"]}. {d["text"]}' for d in corpus]
    qrels = defaultdict(dict)
    for r in qrels_rows:
        qrels[str(r["query-id"])][str(r["corpus-id"])] = int(r["score"])
    qtext = {str(q["_id"]): q["text"] for q in queries}
    test_q = [(qid, qtext[qid]) for qid in qrels]
    return doc_ids, docs, test_q, qrels


# ---------------------------------------------------------------- metrics
def ndcg_at_k(ranked, rels, k=10):
    dcg = sum(rels.get(d, 0) / math.log2(i + 2) for i, d in enumerate(ranked[:k]))
    ideal = sorted(rels.values(), reverse=True)[:k]
    idcg = sum(r / math.log2(i + 2) for i, r in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def recall_at_k(ranked, rels, k):
    relevant = {d for d, r in rels.items() if r > 0}
    return len(relevant & set(ranked[:k])) / len(relevant) if relevant else 0.0


def mrr_at_k(ranked, rels, k=10):
    for i, d in enumerate(ranked[:k]):
        if rels.get(d, 0) > 0:
            return 1.0 / (i + 1)
    return 0.0


def evaluate(run, qrels):
    rows = [
        (ndcg_at_k(r, qrels[q]), recall_at_k(r, qrels[q], 10), recall_at_k(r, qrels[q], 100), mrr_at_k(r, qrels[q]))
        for q, r in run.items()
    ]
    return [sum(col) / len(col) for col in zip(*rows)]


# ---------------------------------------------------------------- retrievers
def bm25_run(doc_ids, docs, queries, k=100):
    retriever = bm25s.BM25()  # Lucene-style BM25, k1=1.5, b=0.75
    retriever.index(bm25s.tokenize(docs, stopwords="en"))
    results, _ = retriever.retrieve(bm25s.tokenize([t for _, t in queries], stopwords="en"), k=k)
    return {qid: [doc_ids[i] for i in row] for (qid, _), row in zip(queries, results)}


def dense_run(doc_ids, doc_emb, q_emb, queries, k=100):
    scores = q_emb @ doc_emb.T  # embeddings are L2-normalised, so dot = cosine
    top = np.argsort(-scores, axis=1)[:, :k]
    return {qid: [doc_ids[i] for i in row] for (qid, _), row in zip(queries, top)}


def rrf(runs, k=60, depth=100):
    """Reciprocal Rank Fusion: score(d) = sum over runs of 1 / (k + rank)."""
    fused = {}
    for qid in runs[0]:
        scores = defaultdict(float)
        for run in runs:
            for rank, d in enumerate(run[qid], start=1):
                scores[d] += 1.0 / (k + rank)
        fused[qid] = sorted(scores, key=scores.get, reverse=True)[:depth]
    return fused


def rerank_run(run, queries, docs_by_id, model_name, top_n=50):
    ce = CrossEncoder(model_name)
    out = {}
    for qid, text in queries:
        cands = run[qid][:top_n]
        scores = ce.predict([(text, docs_by_id[d]) for d in cands], batch_size=64)
        order = np.argsort(-np.asarray(scores))
        out[qid] = [cands[i] for i in order] + run[qid][top_n:]  # keep the tail for Recall@100
    return out


def quantized_runs(doc_ids, doc_emb, q_emb, queries, k=100, rescore_multiplier=4):
    """int8 and binary document embeddings, each with float32 query rescoring."""
    try:  # sentence-transformers >= 5 moved the helper
        from sentence_transformers.util.quantization import quantize_embeddings
    except ImportError:
        from sentence_transformers.quantization import quantize_embeddings

    runs = {}
    # int8: calibrate ranges on the corpus, then score int8 docs against float queries
    d8 = quantize_embeddings(doc_emb, precision="int8", calibration_embeddings=doc_emb).astype(np.float32)
    q8 = quantize_embeddings(q_emb, precision="int8", calibration_embeddings=doc_emb).astype(np.float32)
    runs["dense int8 (4x smaller)"] = dense_run(doc_ids, d8, q8, queries, k)

    # binary: Hamming search on packed bits, then rescore the shortlist with the float query
    db = quantize_embeddings(doc_emb, precision="ubinary")
    qb = quantize_embeddings(q_emb, precision="ubinary")
    unpacked_docs = np.unpackbits(db, axis=1).astype(np.float32) * 2 - 1  # {0,1} -> {-1,+1}
    run = {}
    for i, (qid, _) in enumerate(queries):
        hamming = np.unpackbits(np.bitwise_xor(db, qb[i]), axis=1).sum(axis=1)
        shortlist = np.argsort(hamming)[: k * rescore_multiplier]
        rescored = unpacked_docs[shortlist] @ q_emb[i]  # float query x binary doc
        run[qid] = [doc_ids[j] for j in shortlist[np.argsort(-rescored)][:k]]
    runs["dense binary + rescore (32x smaller)"] = run
    return runs


def splade_run(doc_ids, docs, queries, model_name, k=100):
    """Learned sparse retrieval: the model predicts a weight for every vocabulary term."""
    from sentence_transformers import SparseEncoder

    model = SparseEncoder(model_name)
    d = model.encode_document(docs, batch_size=8, show_progress_bar=True)  # vocab-sized logits: keep batches small
    q = model.encode_query([t for _, t in queries])
    scores = model.similarity(q, d).to_dense().cpu().numpy()  # dot product of sparse vectors
    top = np.argsort(-scores, axis=1)[:, :k]
    return {qid: [doc_ids[i] for i in row] for (qid, _), row in zip(queries, top)}


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--embed-model", default="sentence-transformers/all-MiniLM-L6-v2")
    ap.add_argument("--reranker", default="cross-encoder/ms-marco-MiniLM-L6-v2")
    ap.add_argument("--rerank-top-n", type=int, default=50)
    ap.add_argument("--limit", type=int, default=0, help="evaluate only the first N queries")
    ap.add_argument("--quantization", action="store_true")
    ap.add_argument("--splade", action="store_true", help="add a learned-sparse (SPLADE) run")
    ap.add_argument("--splade-model", default="naver/splade-cocondenser-ensembledistil")
    args = ap.parse_args()

    doc_ids, docs, queries, qrels = load_scifact()
    if args.limit:
        queries = queries[: args.limit]
    print(f"corpus={len(docs)} docs, test queries={len(queries)}\n")
    docs_by_id = dict(zip(doc_ids, docs))

    runs, timings = {}, {}
    t = time.time()
    runs["BM25"] = bm25_run(doc_ids, docs, queries)
    timings["BM25"] = time.time() - t

    t = time.time()
    enc = SentenceTransformer(args.embed_model)
    doc_emb = enc.encode(docs, batch_size=64, normalize_embeddings=True, show_progress_bar=True)
    q_emb = enc.encode([q for _, q in queries], normalize_embeddings=True)
    runs["Dense"] = dense_run(doc_ids, doc_emb, q_emb, queries)
    timings["Dense"] = time.time() - t

    runs["Hybrid (RRF)"] = rrf([runs["BM25"], runs["Dense"]])

    t = time.time()
    runs[f"Hybrid + rerank top-{args.rerank_top_n}"] = rerank_run(
        runs["Hybrid (RRF)"], queries, docs_by_id, args.reranker, args.rerank_top_n
    )
    timings[f"Hybrid + rerank top-{args.rerank_top_n}"] = time.time() - t

    if args.splade:
        t = time.time()
        runs["SPLADE (learned sparse)"] = splade_run(doc_ids, docs, queries, args.splade_model)
        timings["SPLADE (learned sparse)"] = time.time() - t

    if args.quantization:
        runs.update(quantized_runs(doc_ids, doc_emb, q_emb, queries))

    print(f"\n{'system':38s} {'nDCG@10':>8s} {'R@10':>7s} {'R@100':>7s} {'MRR@10':>7s}")
    for name, run in runs.items():
        n, r10, r100, mrr = evaluate(run, qrels)
        extra = f"   ({timings[name]:.0f}s)" if name in timings else ""
        print(f"{name:38s} {n:8.3f} {r10:7.3f} {r100:7.3f} {mrr:7.3f}{extra}")


if __name__ == "__main__":
    main()
