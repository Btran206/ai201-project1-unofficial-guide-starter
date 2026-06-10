"""
Gradio query interface for The Unofficial Guide (Milestone 5).

Wires the existing RAG pipeline to a simple web UI:
    question -> Retriever (local embed + ChromaDB) -> Groq generation -> answer + sources

The model and ChromaDB collection are loaded ONCE at startup and reused for every
query (not reloaded per request).

Usage:
    python app.py
then open the local URL Gradio prints.
"""

from __future__ import annotations

import os

import gradio as gr
from dotenv import load_dotenv
from groq import Groq

from generate import answer_question
from retrieve import Retriever

# --- Load the pipeline once at startup ---
load_dotenv()
_api_key = os.getenv("GROQ_API_KEY")
if not _api_key:
    raise SystemExit("GROQ_API_KEY not found. Add it to your .env file.")

_client = Groq(api_key=_api_key)
_retriever = Retriever()  # loads embedding model + ChromaDB collection once


def ask(question: str) -> dict:
    """End-to-end: retrieve + generate. Returns {'answer', 'sources'}.

    'sources' is a list of human-readable citation strings built programmatically
    from the retrieved chunks' metadata -- NOT left to the LLM to invent.
    """
    result = answer_question(question, _retriever, _client)
    sources = [
        f"{s['metadata']['professor']} - {s['metadata']['course']} "
        f"({s['metadata']['date']}) [similarity {s['similarity']:.2f}]"
        for s in result["sources"]
    ]
    return {"answer": result["answer"], "sources": sources}


def handle_query(question: str):
    question = (question or "").strip()
    if not question:
        return "Please enter a question.", ""
    result = ask(question)
    sources = "\n".join(f"• {s}" for s in result["sources"])
    return result["answer"], sources


with gr.Blocks(title="The Unofficial Guide") as demo:
    gr.Markdown(
        "# The Unofficial Guide\n"
        "Ask about UCSD CS / Data Science professors. Answers are grounded in real "
        "student reviews — every answer lists the reviews it drew from."
    )
    inp = gr.Textbox(
        label="Your question",
        placeholder="e.g. Is Julian McAuley a tough grader?",
    )
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=5)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()
