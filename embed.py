"""
Embedding + vector store for The Unofficial Guide (Milestone 4).

Loads chunks.json, embeds each chunk's `text` with the model specified in
planning.md, and stores the vectors + metadata in a persistent ChromaDB
collection using cosine similarity.

Architecture (planning.md):
  - Embedding model: multi-qa-MiniLM-L6-cos-v1 (sentence-transformers, local CPU)
  - 384-dim vectors, cosine similarity
  - Vector store: ChromaDB (persistent, on disk)

The model auto-downloads from Hugging Face on first run (~90 MB) and is cached
for subsequent runs. Re-running this script rebuilds the collection from scratch
so it stays in sync with chunks.json.

Usage:
    python embed.py
"""

from __future__ import annotations

import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

MODEL_NAME = "multi-qa-MiniLM-L6-cos-v1"
CHUNKS_FILE = Path(__file__).parent / "chunks.json"
CHROMA_DIR = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "professor_reviews"


def load_chunks() -> list[dict]:
    if not CHUNKS_FILE.exists():
        raise SystemExit(f"{CHUNKS_FILE.name} not found -- run `python ingest.py` first.")
    chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
    if not chunks:
        raise SystemExit("chunks.json is empty.")
    return chunks


def main():
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks from {CHUNKS_FILE.name}")

    # Loads from local cache if present, otherwise downloads from Hugging Face.
    print(f"Loading embedding model '{MODEL_NAME}' (first run downloads ~90 MB)...")
    model = SentenceTransformer(MODEL_NAME)
    dim = model.get_sentence_embedding_dimension()
    print(f"Model ready. Embedding dimension: {dim}")

    texts = [c["text"] for c in chunks]
    # normalize_embeddings=True pairs with cosine similarity; this is a -cos- model.
    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,
    ).tolist()

    # Persistent on-disk store (chroma_db/ is gitignored).
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Rebuild from scratch each run so the collection matches chunks.json exactly.
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing '{COLLECTION_NAME}' collection.")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    collection.add(
        ids=[c["id"] for c in chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[c["metadata"] for c in chunks],
    )

    count = collection.count()
    print(f"\nStored {count} vectors in ChromaDB collection '{COLLECTION_NAME}'")
    print(f"Persisted to {CHROMA_DIR}/")

    if count != len(chunks):
        print(f"  ! WARNING: stored {count} but expected {len(chunks)}")

    # --- Sanity query: confirm retrieval works end to end ---
    print("\nSanity check query: 'Which professor gives useful feedback?'")
    q_emb = model.encode(
        ["Which professor gives useful feedback?"],
        normalize_embeddings=True,
    ).tolist()
    res = collection.query(query_embeddings=q_emb, n_results=3)
    for i, (doc, meta, dist) in enumerate(
        zip(res["documents"][0], res["metadatas"][0], res["distances"][0]), 1
    ):
        print(f"  {i}. [{meta['professor']} / {meta['course']}] cosine_dist={dist:.3f}")
        print(f"     {doc[:110]}...")


if __name__ == "__main__":
    main()
