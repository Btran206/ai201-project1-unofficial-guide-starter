"""
Ingestion + chunking for The Unofficial Guide (Milestone 3).

Loads every professor review file in documents/, cleans the review text, and
produces one chunk per review (record-based chunking, no overlap). Output is
written to chunks.json for the embedding step.

Each chunk has two parts:
  - "text":  the part that gets EMBEDDED and searched. We embed only the
             semantically meaningful prose: professor name + tags + comment,
             as one clean line. Numbers, dates, and field labels are excluded
             because they add noise to the meaning vector without helping match
             a natural-language question.
  - "metadata": structured fields NOT embedded -- used for filtering and for
                citing the source in the final answer (course, date, rating,
                difficulty, tags, aggregate professor stats, source file).

Chunking strategy (see planning.md):
  - Chunk size: one review per chunk (~50-130 tokens of prose), variable.
  - Overlap: 0 -- reviews are discrete records; overlap would contaminate them.
  - Cleaning: html.unescape() + whitespace/newline collapse on all text.

Usage:
    python ingest.py
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

DOCUMENTS_DIR = Path(__file__).parent / "documents"
OUTPUT_FILE = Path(__file__).parent / "chunks.json"

# A review file is: a header block, then review blocks separated by "\n---\n".
REVIEW_SEPARATOR = "\n---\n"

# Single-line fields use [^\n]*; Comment uses [\s\S]*? so it can span multiple
# lines (some scraped comments contain embedded newlines) up to the Tags line.
REVIEW_PATTERN = re.compile(
    r"Date:\s*([^\n]*)\n"
    r"Course:\s*([^\n]*)\n"
    r"Rating:\s*([^\n]*)\n"
    r"Difficulty:\s*([^\n]*)\n"
    r"Comment:\s*([\s\S]*?)\n"
    r"Tags:\s*([^\n]*)"
)

HEADER_PATTERN = re.compile(
    r"Professor:\s*([^\n]*)\n"
    r"School:\s*([^\n]*)\n"
    r"Department:\s*([^\n]*)\n"
    r"Overall Quality:\s*([^\n]*)\n"
    r"Would Take Again:\s*([^\n]*)\n"
    r"Difficulty:\s*([^\n]*)\n"
    r"Total Ratings:\s*([^\n]*)"
)


def clean_text(text: str) -> str:
    """Decode HTML entities and collapse all whitespace/newlines to single spaces."""
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def leading_number(value: str) -> float | None:
    """Extract the first number from a string like '5.0 / 5.0' or '100.0%' or '4'."""
    m = re.search(r"-?\d+(?:\.\d+)?", value or "")
    return float(m.group()) if m else None


def parse_header(header_block: str) -> dict:
    """Pull professor identity + aggregate stats for metadata (not embedded)."""
    m = HEADER_PATTERN.search(header_block)
    if not m:
        return {
            "professor": "Unknown",
            "school": "Unknown",
            "department": "Unknown",
            "overall_quality": -1.0,
            "would_take_again_pct": -1.0,
            "avg_difficulty": -1.0,
            "total_ratings": -1.0,
        }
    professor, school, department, quality, wta, difficulty, total = m.groups()
    return {
        "professor": clean_text(professor),
        "school": clean_text(school),
        "department": clean_text(department),
        "overall_quality": leading_number(quality) or -1.0,
        "would_take_again_pct": leading_number(wta) or -1.0,
        "avg_difficulty": leading_number(difficulty) or -1.0,
        "total_ratings": leading_number(total) or -1.0,
    }


def parse_reviews(body: str) -> list[dict]:
    """Split the document body into individual cleaned review records."""
    reviews = []
    for raw_block in body.split(REVIEW_SEPARATOR):
        block = raw_block.strip()
        if not block:
            continue  # skip empty trailing block if the file ends with a separator
        m = REVIEW_PATTERN.search(block)
        if not m:
            print(f"  ! could not parse a review block, skipping:\n    {block[:80]!r}")
            continue
        date, course, rating, difficulty, comment, tags = m.groups()
        reviews.append(
            {
                "date": clean_text(date),
                "course": clean_text(course),
                "rating": leading_number(rating),
                "difficulty": leading_number(difficulty),
                "comment": clean_text(comment),
                "tags": clean_text(tags),
            }
        )
    return reviews


def build_embedding_text(header: dict, review: dict) -> str:
    """Compose the text that gets embedded: professor + tags + comment, one clean line.

    Excludes numbers, dates, and field labels (noise for semantic matching).
    Built from already-cleaned strings, so the result contains no newlines.
    """
    parts = [f"Professor {header['professor']}, {header['department']}."]
    if review["tags"]:
        parts.append(f"Tags: {review['tags']}.")
    if review["comment"]:
        parts.append(review["comment"])
    return " ".join(parts)


def build_chunks() -> list[dict]:
    chunks = []
    files = sorted(DOCUMENTS_DIR.glob("*.txt"))
    if not files:
        raise SystemExit(f"No .txt files found in {DOCUMENTS_DIR}")

    for path in files:
        text = path.read_text(encoding="utf-8")
        parts = text.split(REVIEW_SEPARATOR, 1)
        if len(parts) != 2:
            print(f"  ! {path.name}: no review records found, skipping")
            continue
        header_block, body = parts
        header = parse_header(header_block)
        reviews = parse_reviews(body)
        print(f"  {path.name}: {len(reviews)} reviews")

        for i, review in enumerate(reviews):
            chunks.append(
                {
                    "id": f"{path.stem}__{i}",
                    "text": build_embedding_text(header, review),
                    # ChromaDB metadata must be str/int/float/bool (no None).
                    "metadata": {
                        "professor": header["professor"],
                        "school": header["school"],
                        "department": header["department"],
                        "overall_quality": header["overall_quality"],
                        "would_take_again_pct": header["would_take_again_pct"],
                        "avg_difficulty": header["avg_difficulty"],
                        "total_ratings": header["total_ratings"],
                        "course": review["course"],
                        "date": review["date"],
                        "rating": review["rating"] if review["rating"] is not None else -1.0,
                        "difficulty": review["difficulty"] if review["difficulty"] is not None else -1.0,
                        "tags": review["tags"],
                        "source_file": path.name,
                    },
                }
            )
    return chunks


def main():
    print(f"Loading documents from {DOCUMENTS_DIR}/ ...")
    chunks = build_chunks()
    OUTPUT_FILE.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8")

    sizes = [len(c["text"]) for c in chunks]
    has_newline = sum("\n" in c["text"] for c in chunks)
    print(f"\nWrote {len(chunks)} chunks to {OUTPUT_FILE.name}")
    print(
        f"Embedded text size (chars): min {min(sizes)}, "
        f"mean {round(sum(sizes) / len(sizes))}, max {max(sizes)}"
    )
    print(f"chunks with a newline in embedded text: {has_newline}")
    print("\nExample chunk:\n" + "-" * 60)
    print("text:", chunks[0]["text"])
    print("metadata:", json.dumps(chunks[0]["metadata"], ensure_ascii=False))
    print("-" * 60)


if __name__ == "__main__":
    main()
