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
**Chunk size:** 700 characters

**Overlap:** 0

**Reasoning:** The documents are delimited by `---` so separating by this delimiter will give exactly one review. Doing anything else could cut a single review in half or merge two different reviews into one chunk which would hurt the accuracy of the RAG system. For that same reason there is no overlap. Every chunk fits inside the embedding model's 512-token window so nothing gets truncated.

**Final chunk count:** 211 (one chunk per review, across all 10 professor files).
---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** I chose `multi-qa-MiniLM-L6-cos-v1` (via `sentence-transformers`) over the general-purpose model `all-MiniLM-L6-v2` because it was trained specifically for short natural-language questions matched against passages which makes sense for my use case (a student asks "Which professor gives useful feedback?" against a corpus of reviews). It's also free because it runs locally on the CPU.

**Top-k:** 5 because each chunk is exactly one review. I shouldn't pick a singular review as the correct. Instead, I will use several so i can get a general consensus (e.g. "most students say X, though one disagrees"). Five reviews is a good baseline to start off and I will change accordingly based on the accuracy.

**Production tradeoff reflection:**
- **Accuracy on domain-specific text:** I'd use a higher-quality model (OpenAI `text-embedding-3-small`) if cost wasn't an issue or a larger local model (`all-mpnet-base-v2`, `bge-large-en-v1.5`) against my 5 eval questions. But since my corpus is pretty limited I don't think these options are necesarry. Student reviews vary, so I'd check whether a bigger model retrieves better on that noisy phrasing.
- **Context length:** Not a factor here since each chunk is one short review well under any model's window.
- **Multilingual support:** None. If I expanded to international student forums or non English reviews, I'd switch to a multilingual model like `paraphrase-multilingual-MiniLM-L12-v2` or Cohere's multilingual embed.
- **Latency & cost:** With only 211 chunks, local inference is effective, so latency isn't a concern. In a production setting with thousands or hundreds of thousands of documents is when I would be concerned.

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

```mermaid
flowchart LR
    A["<b>Ingestion</b><br/>Read 10 rate my professor reviews from text files"]
    B["<b>Chunking</b><br/>Split on '---' delimiter<br/>1 review = 1 chunk -> 211 chunks total"]
    C["<b>Embedding + Vector Store</b><br/>Encode chunks to 384-dim vectors,<br/>store with cosine similarity<br/><i>multi-qa-MiniLM-L6-cos-v1<br/> -> ChromaDB</i>"]
    D["<b>Retrieval</b><br/>Embed query, fetch top-k=5<br/>most similar review chunks<br/><i>ChromaDB cosine search</i>"]
    E["<b>Generation</b><br/>Grounded, cited answer from<br/>retrieved reviews + question<br/><i>Groq LLM</i>"]

    A --> B --> C --> D --> E

    Q["User question<br/>e.g. 'Which professor gives useful feedback?'"] --> D
```

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
