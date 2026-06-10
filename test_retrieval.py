"""
Sanity check for retrieval (Milestone 4).

Runs a handful of evaluation queries through the Retriever and prints the
returned chunks with their cosine distance scores, so we can eyeball whether
retrieval is pulling sensible reviews before wiring up generation.

This is NOT the formal evaluation (that lives in planning.md / README and judges
final answers). It only checks the retrieval stage in isolation.

Usage:
    python test_retrieval.py
"""

from __future__ import annotations

from retrieve import Retriever

TOP_K = 5
PREVIEW_CHARS = 160

EVAL_QUERIES = [
    "Which professor gives the most useful feedback?",
    "Is Julian McAuley a tough grader?",
    "Which data science professor has the easiest classes?",
    "Are Soohyun Liao's lectures helpful?",
    "Which professor should I avoid?",
]


def main():
    retriever = Retriever()  # loads model + collection once

    for qi, query in enumerate(EVAL_QUERIES, 1):
        print("=" * 78)
        print(f"Query {qi}: {query}")
        print("=" * 78)

        results = retriever.retrieve(query, top_k=TOP_K)
        for rank, r in enumerate(results, 1):
            m = r["metadata"]
            preview = r["text"][:PREVIEW_CHARS].rstrip()
            if len(r["text"]) > PREVIEW_CHARS:
                preview += "..."
            print(
                f"  [{rank}] distance={r['distance']:.4f}  similarity={r['similarity']:.4f}"
            )
            print(f"      {m['professor']} / {m['course']} ({m['date']})")
            print(f"      {preview}")
        print()


if __name__ == "__main__":
    main()
