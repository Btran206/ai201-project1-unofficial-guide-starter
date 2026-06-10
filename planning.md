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
- **Accuracy on domain-specific text:** I'd use a higher-quality model (OpenAI `text-embedding-3-small`) if cost wasn't an issue or a larger local model (`all-mpnet-base-v2`, `bge-large-en-v1.5`) against my 5 eval questions. But since my corpus is pretty limited I don't think these options are necessary. Student reviews vary, so I'd check whether a bigger model retrieves better on that noisy phrasing.
- **Context length:** Not a factor here since each chunk is one short review well under any model's window.
- **Multilingual support:** None. If I expanded to international student forums or non English reviews, I'd switch to a multilingual model like `paraphrase-multilingual-MiniLM-L12-v2` or Cohere's multilingual embed.
- **Latency & cost:** With only 211 chunks, local inference is effective, so latency isn't a concern. In a production setting with thousands or hundreds of thousands of documents is when I would be concerned.
S
---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer | Why retrieval was strong / weak |
|---|----------|-----------------|---------------------------------|
| 1 | Which professor gives the most useful feedback? | Justin Eldridge — multiple reviews tagged "Gives good feedback"; Rajesh Gupta also noted for answering questions after class. | **Moderate (dist ~0.41–0.46).** The "Gives good feedback" tag is embedded in the chunk text, so it matched directly, but "useful feedback" is a soft concept spread across many reviews, so scores are mid-range rather than tight. |
| 2 | Is Julian McAuley a tough grader? | Yes — widely described as a harsh grader who refuses to curve; many reviews tagged "Tough grader". | **Strong (dist ~0.22–0.27).** Both the professor name and the "Tough grader" tag live in the embedded text, so the query matched the *who* and the *what* at once — all 5 hits were McAuley, tightly clustered. |
| 3 | Which data science professor has the easiest classes? | Ambiguous in the corpus — McAuley's CSE158 is "supposed to be" easy but reviewers say he made it hard; no professor is clearly identified as easiest. | **Weak.** Retrieval matched "data science professor" + positive sentiment and returned all-Justin-Eldridge reviews praising him, but they describe him as *great*, not *easy*. The embedding barely captured the "easiest"/difficulty axis — difficulty is poorly represented in free-text prose. |
| 4 | Are Soohyun Liao's lectures helpful? | Mixed — opinions split: some call her lectures messy and unorganized, others call them amazing and caring. | **Strong (dist ~0.33–0.37).** The professor name anchored every hit to Soohyun Liao, and the returned set is genuinely mixed-sentiment — ideal for a consensus-style answer ("most say X, though some disagree"). |
| 5 | Which professor should I avoid? | Based on lowest ratings / most negative reviews: Julian McAuley (many 1.0 ratings) and Soohyun Liao both have strongly negative reviews. | **Weak / mixed.** It surfaced real negative reviews (Soohyun Liao "worst professor I've ever had"), but hits [1] and [3] were *positive* Gupta reviews. Embeddings capture topic (discussion of professor quality) far better than polarity, so "avoid"/negative queries pull positive and negative reviews alike. |

**What we're doing here and why.** Before building the generation stage, we ran these 5 questions through retrieval (`test_retrieval.py`) and scored each by cosine distance. The point is to separate retrieval quality from generation quality: if a final answer is wrong, we want to know whether the system retrieved the wrong reviews or retrieved the right reviews and then wrote a bad answer. Judging retrieval on its own tells us that. The "Why" column records the diagnosis for each query so the failures are traceable to a specific cause rather than a vague "it didn't work."

The pattern across the five is consistent: retrieval is strong when a query names an entity or a concept that lives in the embedded text (Q2 professor name + "Tough grader" tag; Q4 professor name) and weak when a query depends on an axis the prose doesn't encode well (difficulty (Q3) and sentiment polarity (Q5)). Those two weak cases is why in the generation stage: I will (1)pass each retrieved review to the LLM with its numeric rating and difficulty as supporting evidence, so the model can reason about the difficulty/polarity that the embedding missed; and (2) the grounding prompt instructs the model to report the consensus and the disagreement and to refuse when the reviews don't cover the question, so mixed or off target retrieval produces an honest answer instead of a confidently wrong one.

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
