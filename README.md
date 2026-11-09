<div align="center">

# 🔍 DocuLens — Citation-First RAG Document Copilot

**Upload any PDF and ask questions about it. Get answers with source citations, not hallucinations.**

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=flat-square&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/pgvector-PostgreSQL-blue?style=flat-square&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)
![CI](https://img.shields.io/github/actions/workflow/status/nirmala-sharma/doculens/ci.yml?style=flat-square&label=CI)

🔗 **Live Demo:** [brilliant-beijinho-a6069f.netlify.app](https://brilliant-beijinho-a6069f.netlify.app/)

</div>

---

## What is DocuLens?

DocuLens is a **Retrieval-Augmented Generation (RAG)** system that lets you chat with your own PDF documents — resumes, reports, documentation, research papers — and get answers backed by exact source citations.

You upload a PDF. You ask: *"What projects did this person work on?"*
DocuLens finds the most relevant passages in your document, reranks them for accuracy, and passes the best ones to an LLM. Every fact in the answer is cited inline like **[1]**, with the **page number and the exact supporting quote**, so you can verify it yourself. If the document doesn't contain the answer, DocuLens says so instead of guessing.

**Agent mode:** for hard questions, DocuLens can run as an AI agent. Instead of searching once with your exact words, the LLM decides what to search for and can search again with different words (up to 3 times) before answering.

> ⚠️ **Privacy Notice:** Do not upload confidential or sensitive documents. Uploaded content is stored on the server for querying purposes.


---

## How It Works

```
User uploads PDF
│
▼
Check limits: over 10 MB or 300 pages -> refused (413); damaged PDF -> refused (400)
│
▼
Extract text page by page → split into 150-word chunks (30-word overlap)
→ embed (BAAI/bge-small-en-v1.5) → store in pgvector with file name + page number
│
User asks a question
│
▼
Embed question → vector search in pgvector (top 20, only within the uploaded file)
│
├── best score < 0.10 → "Not found in the document" (no LLM call)
│
▼
Cross-encoder reranker (ms-marco-MiniLM) re-scores the 20 → keeps the best 3
│
▼
LLM (Groq) answers ONLY from the numbered passages, citing facts as [1], [2]
│
▼
Validate citations → remove made-up numbers, renumber the used ones
│
▼
Return answer + citations (file, page, exact supporting quote) + relevance score
```

**Guardrail:** if no passage scores above the similarity threshold, DocuLens refuses to answer instead of guessing, which prevents hallucinated answers to out-of-scope questions.

**How the relevance score works:** pgvector's `<->` operator measures the **L2 (Euclidean) distance**, the straight-line distance between the question's embedding and each chunk's embedding. The score is `1 − distance`, so higher means more similar. Because the BGE model produces normalized vectors (length 1), L2 distance ranks results in exactly the same order as cosine similarity (`L2² = 2 − 2 × cosine`). The score ranges  1 (identical) to -1 (opposite); in testing, answerable questions scored about 0.25–0.55 and out-of-scope questions about -0.06 to 0.06, so the refusal threshold is 0.10.

**Citations you can verify:** for each citation, the reranker picks the single sentence that best supports the answer, so users see the exact quote and the page it came from.

### Agent mode

```
User asks a question (Agent mode on)
│
▼
LLM reads the question and decides what to search for
│
├── calls search_documents("its own search words")
│      → vector search (top 20) → relevance check → rerank → best 3 passages
│      → if nothing relevant: "No relevant passages found. Try different words."
│      → results go back to the LLM
│
├── searches again with different words if needed (max 3 rounds)
│
▼
LLM answers from the passages, citing [1], [2]
(after 3 rounds, the answer is forced with tools turned off)
│
▼
Same citation validation and exact quotes as the normal pipeline
```

The LLM never runs anything itself: it only *asks* for a search, and my code runs it. The search tool is read-only, and my code (not the LLM) decides which document is searched.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| API | FastAPI | Async, auto-docs, type safety |
| Vector DB | PostgreSQL + pgvector | Vector search next to regular data (file name, page), no extra infrastructure |
| Embeddings | fastembed (BAAI/bge-small-en-v1.5) | Lightweight, high quality, runs inside the container |
| Reranker | fastembed cross-encoder (Xenova/ms-marco-MiniLM-L-6-v2) | Re-scores the top 20 passages for accuracy; same library, no new dependency |
| LLM | Groq (openai/gpt-oss-20b) | Fast inference, OpenAI-compatible API, supports tool calling for the agent |
| PDF parsing | pdfplumber | Page-by-page text extraction for page-level citations |
| Frontend | Vanilla HTML/CSS/JS | Zero dependencies, instant load |
| Rate limiting | slowapi | Limits requests per IP address on /ask and /upload |
| Container | Docker Compose | Reproducible dev environment |
| Testing | pytest + two evaluation suites | Unit tests (with a fake LLM for the agent); evaluations for answer quality |
| CI | GitHub Actions | Runs the tests on every push and pull request |
| Hosting | Render (API) + Netlify (frontend) | Free-tier deployment |

---

## Features

- **PDF upload** — upload any PDF and start asking questions immediately
- **Page-level citations** — every fact is cited inline like [1], with the file name, page number, and the exact supporting quote
- **Clickable citations** — click [1] to open the full passage, with your question's key terms highlighted
- **Citation validation** — made-up citation numbers are removed, and only the citations actually used are shown, numbered 1, 2, 3...
- **Reranking** — a cross-encoder re-scores the top 20 search results, so the LLM gets the 3 most relevant passages
- **Agent mode** — an optional tool-calling agent that rewrites and repeats searches when the first one is weak (up to 3 rounds); toggle it with "Agent mode" in the chat
- **Similarity guardrail** — refuses to answer when the document doesn't contain relevant content
- **Upload limits** — PDFs larger than 10 MB or longer than 300 pages are refused with a clear message, and damaged PDFs show an error message instead of crashing the server
- **Rate limiting** — each user (IP address) can ask 10 questions and upload 5 files per minute; extra requests get an error message saying Too Many Requests
- **Source filtering** — answers come only from the document you uploaded, not mixed with others
- **Multiple file support** — upload several PDFs and query across all of them
- **Deduplication** — re-uploading the same file replaces its old chunks, so there are no duplicates
- **Prompt-injection mitigation** — document text is clearly separated from instructions, and the model is told never to follow instructions inside it
- **Safe display** — PDF text is escaped before it's shown in the browser, preventing script injection (XSS)
- **Automatic database setup** — the table, columns, and pgvector extension are created on startup
- **Memory-efficient** — runs in about 400 MB (including Agent mode), fitting a 512 MB free-tier server
- **Chat-style UI** — dark interface with Markdown rendering and a typing indicator

---

## Engineering Highlights

Real problems found through testing, and how they were fixed.

**1. An improvement that made things worse — and why**
After adding reranking, the evaluation score *dropped* from 20/20 to 16/20. Logging what the LLM actually received showed two problems: chunks were ~4,500 characters but the context limit was 4,000, so the LLM only saw part of one chunk; and the reasoning model's thinking used the whole 500-token budget, leaving empty answers. Fixing both restored the score.

| Change | Eval score |
|---|---|
| Original (top 1 chunk, no reranking) | 20/20 |
| Added reranking (context cut off) | 16/20 |
| Fixed context and token limits | 19/20 |
| Page-based chunks + citations | 19/20 |
| Smaller chunks (150 words), 2 sent to the LLM | 18/20 |
| **Smaller chunks, 3 sent to the LLM** | **20/20** |

**2. From 3.5 GB to ~400 MB of memory**
The app worked locally but peaked at ~3.5 GB after a large upload, far above the 512 MB server limit. Measuring each step with `docker stats` found two causes: pdfplumber kept every parsed page in memory, and ONNX Runtime's memory pool kept growing during reranking. Fixes: free each page after extraction, load the embedding model once instead of twice, limit inference threads, disable the memory pool, and rerank in small batches.

| | Before | After |
|---|---|---|
| Idle | 359 MB | 275 MB |
| After a 721-page PDF upload | 3.56 GB | 343 MB |
| After upload + 3 questions | — | ~400 MB |

**3. Not trusting the model's citations**
The model sometimes cited passages in its own trained format (`【1】`) instead of `[1]`, which slipped past validation. Citations are now normalized, checked against the passages actually retrieved, and renumbered, with unit tests covering each case.

**4. A trade-off: chunk size**
Smaller chunks made citations more precise but gave the LLM less context (20 → 18). Since smaller chunks use fewer tokens, sending 3 instead of 2 restored 20/20 while keeping the precise citations.

**5. An agent built to fix measured failures**
The NumPy evaluation scored 20/20, but a harder test on a resume scored 8/11: questions about rare project names (e.g. "What is LogSignals?" scored 0.097, just under the threshold) and a broad question failed because the pipeline searches only once, using the user's exact words. A tool-calling agent that can change the search words and try again fixed all three, without breaking the original set.

| | Pipeline | Agent |
|---|---|---|
| Resume evaluation (11 harder questions) | 8/11 | **11/11** |
| NumPy evaluation (20 questions) | 20/20 | **20/20** |
| Avg answer time (NumPy) | ~2.7 s | ~4.7 s |
| Avg refusal time (NumPy) | ~35 ms | ~2.8 s |

The trade-off is speed: the agent tries several searches before refusing, and each round resends earlier results, which can hit Groq's free-tier limit (8,000 tokens/min). That's handled with automatic retries and a clear "service busy" message instead of a crash. Testing also found two bugs in the step-limit code path, now covered by unit tests with a fake LLM.

---

## Evaluation Results

Tested against the [NumPy User Guide](https://numpy.org/doc/stable/numpy-user.pdf) — a real 700+ page technical document with specific, verifiable facts.

**Score: 20/20 (100%)** — 15 answerable questions (checked for expected keywords) and 5 out-of-scope questions (must be refused).

| # | Question | Result | Latency | Score |
|---|----------|--------|---------|-------|
| 1 | What is a NumPy array? | ✅ | 2808ms | 0.519 |
| 2 | How is a NumPy array different from a Python list? | ✅ | 3205ms | 0.343 |
| 3 | What does the shape attribute of an array represent? | ✅ | 2469ms | 0.333 |
| 4 | What is broadcasting in NumPy? | ✅ | 2613ms | 0.518 |
| 5 | What function creates an array filled with zeros? | ✅ | 2282ms | 0.423 |
| 6 | What is the dtype of a NumPy array? | ✅ | 2547ms | 0.475 |
| 7 | What does np.reshape do? | ✅ | 2255ms | 0.351 |
| 8 | What is a universal function (ufunc) in NumPy? | ✅ | 2973ms | 0.498 |
| 9 | What is the difference between copy and view in NumPy? | ✅ | 3409ms | 0.455 |
| 10 | How do you index a 2D NumPy array? | ✅ | 3004ms | 0.368 |
| 11 | What does np.linspace do? | ✅ | 2896ms | 0.290 |
| 12 | What is axis in NumPy operations? | ✅ | 2803ms | 0.383 |
| 13 | What does np.concatenate do? | ✅ | 2788ms | 0.306 |
| 14 | What is the purpose of np.arange? | ✅ | 2695ms | 0.260 |
| 15 | What does the transpose operation do to an array? | ✅ | 2490ms | 0.342 |
| 16 | What is the weather in New York today? *(out of scope)* | ✅ | 33ms | -0.003 |
| 17 | Who is the current president of the United States? *(out of scope)* | ✅ | 35ms | -0.045 |
| 18 | What is the capital of France? *(out of scope)* | ✅ | 36ms | -0.056 |
| 19 | How do I make pasta? *(out of scope)* | ✅ | 33ms | 0.062 |
| 20 | What is the stock price of Apple? *(out of scope)* | ✅ | 35ms | 0.038 |

> **Answerable questions:** ~2.7 s average (search + reranking + LLM on Groq's free tier), measured locally.
> **Out-of-scope questions:** refused in ~35 ms average, because the guardrail stops them before the LLM is called.
> **Trade-off:** the memory optimizations (no ONNX memory pool, smaller rerank batches) raised average latency from ~1.4 s to ~2.7 s, in exchange for fitting a 512 MB server.

### Agent mode and the harder resume evaluation

A second suite (`tests/evaluation_resume.py`) uses 11 harder questions on a resume: rare names, exact numbers, broad questions, and questions that must be refused. It also checks that the expected facts appear in the **cited passages**, not just the answer.

| Suite | Pipeline | Agent |
|---|---|---|
| NumPy (20 questions) | 20/20 | 20/20 |
| Resume (11 questions) | 8/11 | 11/11 |

Each suite was run once; LLM results can vary slightly between runs. Set `USE_AGENT = True` or `False` at the top of either script to choose the mode.

**To reproduce:**
1. Download [numpy-user.pdf](https://numpy.org/doc/stable/numpy-user.pdf) and place it in the project root
2. Start the backend with `docker compose up -d`
3. Run `python tests/evaluation.py`

---

## Project Structure
```
doculens/
├── app/
│   ├── api/
│   │   ├── ask.py              # Pipeline: search → guardrail → rerank → LLM → citation validation
│   │   ├── agent.py            # Agent: search tool, tool-calling loop (max 3 rounds)
│   │   └── search.py           # Vector search (pgvector), reranking, page lookup
│   ├── db/
│   │   └── schema.py           # Creates the pgvector extension, table, and columns on startup
│   └── main.py                 # FastAPI app: /ask, /upload, /health,     upload limits, rate limiting
├── scripts/
│   ├── ingest.py               # PDF → pages → chunks → embeddings → database
│   ├── try_rerank.py           # Reranker demo on a controlled example
│   ├── compare_rerank.py       # Shows chunk order before vs. after reranking on real data
│   └── try_agent.py            # Walks through one tool-calling round step by step
├── frontend/
│   └── index.html              # Chat UI with clickable citation cards and Agent mode toggle
├── tests/
│   ├── test_health.py          # Health endpoint test
│   ├── test_citations.py       # Citation validation + guardrail regression tests
│   ├── test_agent.py           # Agent tests with a fake LLM (search, step limit)
│   ├── evaluation.py           # 20-question evaluation (NumPy guide)
│   └── evaluation_resume.py    # 11 harder questions (resume)
├── .github/workflows/
│   └── ci.yml                  # GitHub Actions CI
├── .dockerignore               # Keeps venv, .env, PDFs out of Docker images
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Running Locally

**Prerequisites:** Docker Desktop

1. Clone the repo
```bash
git clone https://github.com/nirmala-sharma/doculens.git
cd doculens
```

2. Create `.env` file
```env
DATABASE_URL=postgresql://postgres:password@db:5432/doculens_db
GROQ_API_KEY=your_groq_api_key_here
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=doculens_db
```
Get a free Groq API key at https://console.groq.com

3. Start the stack
```bash
docker compose up --build
```

4. Open `frontend/index.html` in your browser (use Live Server in VS Code), or visit http://localhost:8000/docs for the API playground

5. Upload a PDF and start asking questions

---

## API

**POST /upload** — ingest a PDF

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@resume.pdf"
```

Response:
```json
{ "message": "'resume.pdf' uploaded and ingested successfully." }
```

**POST /ask** — ask a question

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What projects are listed?", "source": "resume.pdf"}'
```

Add `"use_agent": true` to use Agent mode (default: `false`):

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is LogSignals?", "source": "resume.pdf", "use_agent": true}'
```

Response (`top_score` is `null` in Agent mode, since the agent may run several searches):
```json
{
  "answer": "Nirmala contributed to Center Randomize with four merged pull requests [1].",
  "sources": ["resume.pdf"],
  "citations": [
    {
      "id": 1,
      "source": "resume.pdf",
      "page": 1,
      "quote": "Contribution: 4 merged pull requests that fixed a command-line crash and added school/center search and a corrected map.",
      "snippet": "...full passage the quote came from..."
    }
  ],
  "top_score": 0.139
}
```
**Errors**

| Status | When |
|---|---|
| 400 | Not a PDF, or the PDF is damaged and can't be read |
| 413 | File is over 10 MB or has more than 300 pages |
| 429 | Too many requests: more than 10 questions or 5 uploads per minute from the same IP address |

**GET /health**
```json
{ "status": "ok", "service": "Doculens-api", "version": "0.1.0" }
```

---

## Key Design Decisions

**Why pgvector instead of a dedicated vector DB (Pinecone, Weaviate)?**
PostgreSQL with pgvector keeps the stack simple — one database handles both metadata and vectors. For a small-scale deployment, this avoids unnecessary infrastructure complexity, and one SQL query can filter by document and rank by meaning.

**Why fastembed instead of sentence-transformers?**
fastembed is ~60MB vs ~500MB for sentence-transformers. In a Docker container this means significantly faster builds and less memory usage, with comparable embedding quality for English text.

**Why a similarity guardrail?**
Without it, the LLM would attempt to answer out-of-scope questions using irrelevant context, producing confident but wrong answers. The guardrail makes the system say "I don't know" instead of hallucinating.

**Why source filtering?**
When multiple PDFs are ingested, without filtering the search returns chunks from all documents. Filtering by `source` ensures answers come only from the document the user uploaded in that session.

**Why lazy Groq client initialization?**
Creating the client at module import time requires GROQ_API_KEY immediately. This broke CI where the key lives in secrets. Lazy init defers the check until an actual API call is made.

**Why L2 distance?**
pgvector's `<->` measures the straight-line distance between two embeddings: smaller distance means more similar meaning. My embeddings are normalized (all the same length), so this gives the same ranking as cosine similarity.

**Why reranking?**
Vector search is fast but sometimes ranks a passage that only shares words with the question above one that actually answers it. A reranker reads the question and passage together, so it's more accurate. I search for 20 passages, then the reranker picks the best 3.

**Why 150-word chunks, split page by page?**
Splitting each page separately means every chunk belongs to one page, which makes page citations possible. Smaller chunks make citations more precise. I chose the size by comparing evaluation scores.

**Why check the LLM's citations?**
The LLM can cite a passage that doesn't exist or use a different format. My code fixes the format, removes fake citations, and shows only the ones actually used.

**Why create the database tables on startup?**
So anyone can clone the project and run it without setting up the database by hand.

**Why limit threads and memory use?**
The free server has only 512 MB of memory. Limiting threads and processing in smaller batches brought memory down from about 3.5 GB to about 400 MB, at the cost of slightly slower answers.

**Why an agent, and why optional?**
A harder evaluation showed the single-search pipeline failing on rare names and broad questions. The agent fixed them, but it's slower and uses more tokens, so it's a toggle: the pipeline stays the default for speed.

**Why build the agent loop by hand instead of using LangChain or LangGraph?**
To understand and control every step: the model requests a tool, my code runs it, and the result goes back. A framework would make sense for bigger multi-step workflows.

**How is the agent kept safe?**
Its only tool is read-only search. My code sets which document is searched, so the LLM can't search other documents. It's limited to 3 rounds, it must answer only from returned passages, and its answers go through the same citation checks.

**Why upload limits and rate limiting?**
Without them, one very large PDF could use up the 512 MB server's memory, and a script sending hundreds of questions could use up the Groq free-tier limit for everyone. Limits are checked before the expensive work (parsing, embedding, LLM calls) starts. On Render, the app reads the real client IP from the `X-Forwarded-For` header, so each user gets their own limit instead of sharing one.

---

## Running Tests

```bash
# Unit tests (no database or API key needed — these run in CI)
pytest tests/ -v

# Full RAG evaluation suite (needs the app running: docker compose up -d)
python tests/evaluation.py
python tests/evaluation_resume.py
```

- **Unit tests:** health endpoint, citation validation (made-up citations removed, `【1】` normalized, renumbering), a regression test for the refusal path, agent tests that use a fake LLM (direct answer, search then answer, step limit), upload limits (too large, too many pages, damaged PDF), and rate limiting (the 6th upload in a minute gets 429).
- **Evaluation suites:** 20 questions on the 721-page NumPy User Guide (`evaluation.py`) and 11 harder questions on a resume (`evaluation_resume.py`), run manually.

CI runs automatically on every push to `main` and `develop`.

---

## Roadmap

- [x] RAG evaluation suite with 20 test cases (keyword + refusal accuracy)
- [x] Markdown rendering in answers
- [x] Cross-encoder reranking
- [x] Page-level citations with exact supporting quotes
- [x] Citation validation (made-up citations removed, renumbering)
- [x] Memory optimization for a 512 MB server
- [x] Agentic RAG: the LLM can rephrase and search again when results are weak (read-only tools)
- [x] Upload limits (file size and page count)
- [x] Rate limiting on /ask and /upload
- [ ] Structured output for the final answer
- [ ] Retrieval strategy comparison: BM25 and hybrid search with Reciprocal Rank Fusion, measured with Hit@k and MRR
- [ ] Cleaner PDF text extraction (some PDFs produce words glued together)
- [ ] User authentication (JWT) for private document isolation
- [ ] Per-session document management (list/delete uploaded files)
- [ ] Upgrade evaluation to RAGAS (faithfulness + answer relevancy scoring)
- [ ] Streaming responses
- [ ] Multi-turn conversation with memory
