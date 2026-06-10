"""
Grounded generation for The Unofficial Guide (Milestone 5).

Pipeline: question -> retrieve top-k review chunks -> build a metadata-rich,
grounded prompt -> call Groq -> return a cited answer.

Groq is used ONLY for the final generation step. Retrieval is fully local
(sentence-transformers + ChromaDB); the LLM never influences which chunks are
returned and only writes the answer from the chunks it is handed.

Grounding mechanisms (see README):
  1. The system prompt restricts the model to the provided reviews, requires
     inline citations (professor, course, date), and tells it to report the
     consensus/spread instead of a single verdict.
  2. Each review in the context carries its numeric rating + difficulty + tags
     as SUPPORTING evidence -- the prose stays the substance, but the numbers
     help the difficulty/sentiment questions where prose-only retrieval was weak.
     The model may only cite numbers that are shown to it (no invented averages).

Usage:
    python generate.py "Is Julian McAuley a tough grader?"
    python generate.py            # interactive loop
"""

from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv
from groq import Groq

from retrieve import DEFAULT_TOP_K, Retriever

# Current Groq production model; swap if you prefer a smaller/faster one
# (e.g. "llama-3.1-8b-instant").
GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are The Unofficial Guide, an assistant that answers questions about \
UCSD data science and computer science professors using ONLY the real student reviews provided \
to you in each request.

Follow these rules strictly:
- Answer only from the reviews given in the context. Do not use outside knowledge or assumptions.
- If the reviews don't contain enough information to answer, say so plainly \
(e.g. "The available reviews don't really cover that.").
- Report the consensus AND the disagreement. When reviews conflict, say so \
(e.g. "Most reviews describe him as a tough grader, though one student disagrees.").
- Cite your sources inline as (Professor, Course, Date), e.g. (McAuley, CSE258, 2025).
- The prose is your primary evidence. You MAY mention a review's numeric rating or difficulty, \
but ONLY when it is shown in that review's context line. Never invent, average, or compute \
numbers that were not given to you.
- Be concise and grounded. Prefer paraphrasing what students actually wrote over generic advice."""


def extract_comment(text: str, professor: str, department: str, tags: str) -> str:
    """Recover just the student comment from a chunk's embedded text.

    Chunk text was built as: "Professor {name}, {dept}. [Tags: {tags}.] {comment}".
    We strip the known prefix so the context shows the comment cleanly; falls back
    to the full text if the prefix doesn't match.
    """
    body = text
    prefix = f"Professor {professor}, {department}."
    if body.startswith(prefix):
        body = body[len(prefix):].lstrip()
    if tags:
        tag_part = f"Tags: {tags}."
        if body.startswith(tag_part):
            body = body[len(tag_part):].lstrip()
    return body


def build_context(results: list[dict]) -> str:
    """Format retrieved chunks into numbered, metadata-rich review blocks."""
    blocks = []
    for i, r in enumerate(results, 1):
        m = r["metadata"]
        comment = extract_comment(r["text"], m["professor"], m["department"], m["tags"])
        rating = m["rating"]
        difficulty = m["difficulty"]
        rating_str = f"{rating}/5" if rating is not None and rating >= 0 else "N/A"
        diff_str = f"{difficulty}/5" if difficulty is not None and difficulty >= 0 else "N/A"
        tags_str = m["tags"] if m["tags"] else "none"
        blocks.append(
            f"[Review {i}] cite as ({m['professor']}, {m['course']}, {m['date']})\n"
            f"  rating: {rating_str} | difficulty: {diff_str} | tags: {tags_str}\n"
            f"  \"{comment}\""
        )
    return "\n\n".join(blocks)


def answer_question(
    question: str,
    retriever: Retriever,
    client: Groq,
    top_k: int = DEFAULT_TOP_K,
) -> dict:
    """Retrieve, build a grounded prompt, and return the model's cited answer."""
    results = retriever.retrieve(question, top_k=top_k)
    context = build_context(results)

    user_message = (
        f"Question: {question}\n\n"
        f"Student reviews:\n{context}\n\n"
        f"Answer the question using only these reviews, following all the rules."
    )

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,  # low -> stay close to the source reviews
    )
    return {
        "answer": response.choices[0].message.content,
        "sources": results,
    }


def _print_answer(result: dict) -> None:
    print("\n" + result["answer"] + "\n")
    print("Sources used:")
    for i, r in enumerate(result["sources"], 1):
        m = r["metadata"]
        print(
            f"  [{i}] {m['professor']} / {m['course']} ({m['date']}) "
            f"| similarity={r['similarity']:.3f}"
        )


def main():
    parser = argparse.ArgumentParser(description="Ask The Unofficial Guide a question.")
    parser.add_argument("question", nargs="?", help="Question (omit for interactive mode).")
    parser.add_argument("--k", type=int, default=DEFAULT_TOP_K, help=f"Top-k (default {DEFAULT_TOP_K}).")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise SystemExit("GROQ_API_KEY not found. Add it to your .env file.")

    client = Groq(api_key=api_key)
    retriever = Retriever()  # load model + collection once

    if args.question:
        _print_answer(answer_question(args.question, retriever, client, top_k=args.k))
        return

    print("The Unofficial Guide -- ask about UCSD CS/DS professors. Ctrl+C to quit.")
    try:
        while True:
            q = input("\n> ").strip()
            if not q:
                continue
            _print_answer(answer_question(q, retriever, client, top_k=args.k))
    except (KeyboardInterrupt, EOFError):
        print("\nBye.")


if __name__ == "__main__":
    main()
