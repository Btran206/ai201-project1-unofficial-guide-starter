"""
Scrape Rate My Professors reviews for a fixed list of professors and write
one plain-text corpus file per professor into documents/.

Uses RMP's unofficial GraphQL endpoint (the same one their website calls).
No paraphrasing — reviews are written out as-is in the project's review format.

Usage:
    1. Edit PROFESSORS below.
    2. python scrape_reviews.py
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests

# --- Edit this list. Each entry: ("Professor Name", "School Name") ---
PROFESSORS = [
    ("Rose Yu", "University of California San Diego"),
    ("Brad Voytek", "University of California San Diego"),
    ("Arun Kumar", "University of California San Diego"),
    ("Soohyun Liao", "University of California San Diego"),
    ("Justin Eldridge", "University of California San Diego"),
    ("Rajesh Gupta", "University of California San Diego"),
    ("Julian McAuley", "University of California San Diego"),
    ("Gal Mishne", "University of California San Diego"),
    ("Jingbo Shang", "University of California San Diego"),
    ("Vineet Bafna", "University of California San Diego"),
    
]

OUTPUT_DIR = Path(__file__).parent / "documents"
GRAPHQL_URL = "https://www.ratemyprofessors.com/graphql"

# This Basic-auth token is hardcoded in RMP's public frontend bundle
# (base64 of "test:test"); it is the same for every visitor.
HEADERS = {
    "Authorization": "Basic dGVzdDp0ZXN0",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (student RAG project)",
}

REQUEST_DELAY_SEC = 0.5  # be polite — throttle between requests


def gql(query: str, variables: dict) -> dict:
    """Run a GraphQL query and return the `data` object, raising on errors."""
    resp = requests.post(
        GRAPHQL_URL,
        headers=HEADERS,
        json={"query": query, "variables": variables},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"], indent=2))
    time.sleep(REQUEST_DELAY_SEC)
    return payload["data"]


SCHOOL_SEARCH = """
query SearchSchool($text: String!) {
  newSearch {
    schools(query: {text: $text}) {
      edges { node { id name city state } }
    }
  }
}
"""

TEACHER_SEARCH = """
query SearchTeacher($text: String!, $schoolID: ID!) {
  newSearch {
    teachers(query: {text: $text, schoolID: $schoolID}) {
      edges { node { id firstName lastName school { name } } }
    }
  }
}
"""

TEACHER_HEADER = """
query TeacherHeader($id: ID!) {
  node(id: $id) {
    ... on Teacher {
      firstName
      lastName
      avgRating
      avgDifficulty
      numRatings
      wouldTakeAgainPercent
      department
      school { name }
    }
  }
}
"""

RATINGS_PAGE = """
query Ratings($id: ID!, $cursor: String) {
  node(id: $id) {
    ... on Teacher {
      ratings(first: 20, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        edges { node {
          date
          class
          clarityRating
          helpfulRating
          difficultyRating
          comment
          ratingTags
        }}
      }
    }
  }
}
"""


def find_school_id(school_name: str) -> str | None:
    edges = gql(SCHOOL_SEARCH, {"text": school_name})["newSearch"]["schools"]["edges"]
    if not edges:
        return None
    return edges[0]["node"]["id"]


def find_teacher_id(name: str, school_id: str) -> str | None:
    edges = gql(TEACHER_SEARCH, {"text": name, "schoolID": school_id})["newSearch"][
        "teachers"
    ]["edges"]
    if not edges:
        return None
    # Prefer an exact case-insensitive full-name match; otherwise take the first hit.
    name_lower = name.strip().lower()
    for e in edges:
        n = e["node"]
        full = f"{n['firstName']} {n['lastName']}".strip().lower()
        if full == name_lower:
            return n["id"]
    return edges[0]["node"]["id"]


def fetch_all_ratings(teacher_id: str) -> list[dict]:
    cursor, out = None, []
    while True:
        ratings = gql(RATINGS_PAGE, {"id": teacher_id, "cursor": cursor})["node"][
            "ratings"
        ]
        out += [e["node"] for e in ratings["edges"]]
        if not ratings["pageInfo"]["hasNextPage"]:
            break
        cursor = ratings["pageInfo"]["endCursor"]
    return out


def fmt_date(raw: str) -> str:
    # RMP returns e.g. "2025-12-22 16:00:00 +0000 UTC" — keep just the date.
    if not raw:
        return "unknown"
    return raw.split(" ")[0]


def fmt_tags(raw: str) -> str:
    # Tags arrive as a single string joined by "--".
    if not raw:
        return ""
    return ", ".join(t.strip() for t in raw.split("--") if t.strip())


def quality(rating: dict) -> float:
    # RMP shows per-review "Quality" as the average of clarity + helpfulness.
    return round((rating["clarityRating"] + rating["helpfulRating"]) / 2, 1)


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def build_document(header: dict, ratings: list[dict]) -> str:
    wta = header.get("wouldTakeAgainPercent")
    wta_str = f"{wta:.1f}%" if wta is not None and wta >= 0 else "N/A"

    lines = [
        f"Professor: {header['firstName']} {header['lastName']}",
        f"School: {header['school']['name']}",
        f"Department: {header.get('department') or 'N/A'}",
        f"Overall Quality: {header['avgRating']:.1f} / 5.0",
        f"Would Take Again: {wta_str}",
        f"Difficulty: {header['avgDifficulty']:.1f} / 5.0",
        f"Total Ratings: {header['numRatings']}",
        "",
    ]

    for r in ratings:
        lines += [
            "---",
            f"Date: {fmt_date(r['date'])}",
            f"Course: {r.get('class') or 'N/A'}",
            f"Rating: {quality(r):.1f}",
            f"Difficulty: {r['difficultyRating']:.1f}",
            f"Comment: {(r.get('comment') or '').strip()}",
            f"Tags: {fmt_tags(r.get('ratingTags'))}",
            "",
        ]

    return "\n".join(lines).rstrip() + "\n"


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    for name, school in PROFESSORS:
        print(f"\n=== {name} @ {school} ===")
        try:
            school_id = find_school_id(school)
            if not school_id:
                print(f"  ! school not found: {school}")
                continue

            teacher_id = find_teacher_id(name, school_id)
            if not teacher_id:
                print(f"  ! professor not found: {name}")
                continue

            header = gql(TEACHER_HEADER, {"id": teacher_id})["node"]
            ratings = fetch_all_ratings(teacher_id)
            print(f"  fetched {len(ratings)} reviews")

            doc = build_document(header, ratings)
            out_path = OUTPUT_DIR / f"{slugify(name)}.txt"
            out_path.write_text(doc, encoding="utf-8")
            print(f"  wrote {out_path.relative_to(Path(__file__).parent)}")
        except Exception as e:
            print(f"  ! failed: {e}")


if __name__ == "__main__":
    main()
