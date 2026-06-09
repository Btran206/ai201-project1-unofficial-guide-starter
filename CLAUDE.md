# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
The domain i chose is student reviews of professors at UCSD in the halıcıoğlu data science institute. This is knowledge is valuable because finding a teacher that suits your preferences or just finding out in general if a teacher is good or not is important for student success. It's usually hard to find this information because student experiences vary getting a general consensus is definitely helpful.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Rate My Professors — Rose Yu | Student reviews of CSE/DSC professor Rose Yu (Computer Science), 7 reviews | `documents/rose_yu.txt` |
| 2 | Rate My Professors — Brad Voytek | Student reviews of professor Brad Voytek (Cognitive Science), 22 reviews | `documents/brad_voytek.txt` |
| 3 | Rate My Professors — Arun Kumar | Student reviews of professor Arun Kumar (Computer Science), 4 reviews | `documents/arun_kumar.txt` |
| 4 | Rate My Professors — Soohyun Liao | Student reviews of professor Soohyun Liao (Data Science), 55 reviews | `documents/soohyun_liao.txt` |
| 5 | Rate My Professors — Justin Eldridge | Student reviews of professor Justin Eldridge (Data Science), 27 reviews | `documents/justin_eldridge.txt` |
| 6 | Rate My Professors — Rajesh Gupta | Student reviews of professor Rajesh Gupta (Computer Science), 9 reviews | `documents/rajesh_gupta.txt` |
| 7 | Rate My Professors — Julian McAuley | Student reviews of professor Julian McAuley (Computer Science), 60 reviews | `documents/julian_mcauley.txt` |
| 8 | Rate My Professors — Gal Mishne | Student reviews of professor Gal Mishne (Computer Science), 5 reviews | `documents/gal_mishne.txt` |
| 9 | Rate My Professors — Jingbo Shang | Student reviews of professor Jingbo Shang (Data Science), 16 reviews | `documents/jingbo_shang.txt` |
| 10 | Rate My Professors — Vineet Bafna | Student reviews of professor Vineet Bafna (Computer Science), 6 reviews | `documents/vineet_bafna.txt` |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->
     
---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
