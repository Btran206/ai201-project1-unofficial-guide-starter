"""
Retrieval for The Unofficial Guide (Milestone 4).

Embeds a user's question with the SAME model used for indexing, then queries the
ChromaDB collection for the top-k most similar review chunks (cosine similarity).
Returns each chunk's text + metadata + score so the generation step can build a
grounded, cited answer.

Design (planning.md):
  - Same embedding model as embed.py, same normalization -- query and chunk
    vectors must live in the same space or distances are meaningless.
  - top-k = 5: one review per chunk, so we pull several to form a consensus
    rather than trusting a single review.

The Retriever class loads the model + collection once and is reused across many
queries (the generation step instantiates it a single time).

Usage:
    python retrieve.py "Which professor gives useful feedback?"
    python retrieve.py "Is Julian McAuley a tough grader?" --k 3
"""

from __future__ import annotations

import argparse

import chromadb
from sentence_transformers import SentenceTransformer

from embed import CHROMA_DIR, COLLECTION_NAME, MODEL_NAME

DEFAULT_TOP_K = 5


class Retriever:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model = SentenceTransformer(model_name)
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        try:
            self.collection = client.get_collection(COLLECTION_NAME)
        except Exception as e:
            raise SystemExit(
                f"Collection '{COLLECTION_NAME}' not found ({e}). "
                f"Run `python embed.py` first to build the vector store."
            )

    def retrieve(self, query: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
        """Return the top_k most similar review chunks for a query.

        Each result: {id, text, metadata, distance, similarity}, best first.
        """
        # Same normalization as indexing so cosine distances are comparable.
        query_embedding = self.model.encode(
            [query], normalize_embeddings=True
        ).tolist()

        res = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        results = []
        for id_, doc, meta, dist in zip(
            res["ids"][0],
            res["documents"][0],
            res["metadatas"][0],
            res["distances"][0],
        ):
            results.append(
                {
                    "id": id_,
                    "text": doc,
                    "metadata": meta,
                    "distance": dist,
                    # Chroma cosine "distance" is 1 - cosine_similarity.
                    "similarity": 1.0 - dist,
                }
            )
        return results


def _format_result(rank: int, r: dict) -> str:
    m = r["metadata"]
    return (
        f"[{rank}] {m['professor']} - {m['course']} "
        f"({m['date']}, rating {m['rating']}, difficulty {m['difficulty']}) "
        f"| similarity={r['similarity']:.3f}\n"
        f"    {r['text']}"
    )


def main():
    parser = argparse.ArgumentParser(description="Retrieve review chunks for a query.")
    parser.add_argument("query", help="The question to search for.")
    parser.add_argument(
        "--k", type=int, default=DEFAULT_TOP_K, help=f"Top-k (default {DEFAULT_TOP_K})."
    )
    args = parser.parse_args()

    retriever = Retriever()
    results = retriever.retrieve(args.query, top_k=args.k)

    print(f"\nQuery: {args.query}")
    print(f"Top {len(results)} results:\n" + "=" * 70)
    for i, r in enumerate(results, 1):
        print(_format_result(i, r))
        print("-" * 70)


if __name__ == "__main__":
    main()
