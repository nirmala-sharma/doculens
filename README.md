# 🔍 DocuLens — Citation-First RAG Support Copilot

> Ask questions about developer documentation. Get answers with source citations, not hallucinations.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=flat-square&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/pgvector-PostgreSQL-blue?style=flat-square&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)
![CI](https://img.shields.io/github/actions/workflow/status/nirmala-sharma/doculens/ci.yml?style=flat-square&label=CI)

---

## What is DocuLens?

DocuLens is a **Retrieval-Augmented Generation (RAG)** system that answers developer questions using only official documentation — no hallucinations, every answer backed by a source.

You ask: *"How do I define a POST endpoint in FastAPI?"*
DocuLens retrieves the most relevant documentation chunks, passes them to an LLM, and returns an answer with the exact source files cited.

---

## How It Works

```
User Question
     │
     ▼
Embed question with BAAI/bge-small-en-v1.5
     │
     ▼
Search pgvector DB (cosine similarity)
     │
     ├── top score < 0.3 → "Not found in docs" (no LLM call)
     │
     ▼
Build context from top 5 chunks
     │
     ▼
LLM (Groq) answers using ONLY the context
     │
     ▼
Return answer + source filenames + confidence score
```

**Guardrail:** If no chunk scores above 0.3 similarity, the system refuses to answer rather than guessing. This prevents hallucination on out-of-scope questions.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| API | FastAPI | Async, auto-docs, type safety |
| Vector DB | PostgreSQL + pgvector | Cosine similarity search at scale |
| Embeddings | BAAI/bge-small-en-v1.5 | Fast, high quality, open source |
| LLM | Groq (openai/gpt-oss-20b) | Low latency inference |
| Frontend | Vanilla HTML/CSS/JS | Zero dependencies, instant load |
| Container | Docker Compose | Reproducible dev environment |
| CI | GitHub Actions | Automated testing on every push |

---

## Project Structure

```
doculens/
├── app/
│   ├── api/
│   │   ├── ask.py        # RAG pipeline: search → LLM → answer
│   │   └── search.py     # Vector search with pgvector
│   ├── ingest/
│   │   └── ingest.py     # Doc chunking + embedding + DB insert
│   └── main.py           # FastAPI app + CORS + /ask endpoint
├── frontend/
│   └── index.html        # Single-page UI
├── tests/
│   └── test_api.py       # Pytest test suite
├── .github/
│   └── workflows/
│       └── ci.yml        # GitHub Actions CI
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Running Locally

**Prerequisites:** Docker Desktop, Python 3.11+

1. Clone the repo
```
   git clone https://github.com/nirmala-sharma/doculens.git
   cd doculens
```

2. Create `.env` file
```
   DATABASE_URL=postgresql://postgres:password@db:5432/doculens_db
   GROQ_API_KEY=your_groq_api_key_here
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=password
   POSTGRES_DB=doculens_db
```
   Get a free Groq API key at https://console.groq.com

3. Start the stack
```
   docker compose up --build
```

4. Ingest documentation
```
   python -m app.ingest.ingest
```

5. Open `frontend/index.html` with Live Server in VS Code, or visit http://localhost:8000/docs for the API playground

---

## API

POST /ask

```
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I add middleware in FastAPI?"}'
```

Response:
```
{
  "answer": "You can add middleware using app.add_middleware()...",
  "sources": ["middleware.md", "tutorial/index.md"],
  "top_score": 0.612
}
```

GET /health returns:
```
{ "status": "ok", "service": "Doculens-api", "version": "0.1.0" }
```

---

## Key Design Decisions

**Why pgvector instead of a dedicated vector DB (Pinecone, Weaviate)?**
PostgreSQL with pgvector keeps the stack simple — one database handles both metadata and vectors. For a portfolio project and small-scale deployment, this avoids unnecessary infrastructure complexity.

**Why a similarity guardrail at 0.3?**
Without it, the LLM would attempt to answer out-of-scope questions using irrelevant context, producing confident but wrong answers. The guardrail makes the system say "I don't know" instead of hallucinating.

**Why lazy Groq client initialization?**
Creating the client at module import time requires GROQ_API_KEY to exist immediately. This broke CI where the key lives in secrets. Lazy init defers the check until an actual API call is made.

---

## Running Tests

```
pytest tests/ -v
```

CI runs automatically on every push to main and develop.

---

## Roadmap

- [ ] Cloud deployment (Render + Netlify)
- [ ] Support multiple documentation sources
- [ ] Evaluation suite with golden Q&A dataset
- [ ] Streaming responses
- [ ] Markdown rendering in frontend


