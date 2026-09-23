
# 🔍 DocuLens — Citation-First RAG Document Copilot
 
> Upload any PDF and ask questions about it. Get answers with source citations, not hallucinations.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=flat-square&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/pgvector-PostgreSQL-blue?style=flat-square&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)
![CI](https://img.shields.io/github/actions/workflow/status/nirmala-sharma/doculens/ci.yml?style=flat-square&label=CI)
 
---
 
## What is DocuLens?
 
DocuLens is a **Retrieval-Augmented Generation (RAG)** system that lets you chat with your own PDF documents — resumes, reports, documentation, research papers — and get answers backed by exact source citations.
 
You upload a PDF. You ask: *"What projects did this person work on?"*
DocuLens embeds your question, retrieves the most relevant chunks from your document, passes them to an LLM, and returns a grounded answer with the source file cited.
 
---
 
## 🖼️ Demo
 
🔗 **Live Demo:** https://brilliant-beijinho-a6069f.netlify.app/
 
---
 
## How It Works
 
```
User uploads PDF
     │
     ▼
Extract text → chunk → embed (BAAI/bge-small-en-v1.5) → store in pgvector
     │
User asks a question
     │
     ▼
Embed question → cosine similarity search in pgvector
     │
     ├── top score < 0.10 → "Not found in docs" (no LLM call)
     │
     ▼
Build context from top chunk(s), filtered by uploaded source
     │
     ▼
LLM (Groq) answers using ONLY the retrieved context
     │
     ▼
Return answer + source filenames + confidence score
```
 
**Guardrail:** If no chunk scores above the similarity threshold, the system refuses to answer rather than guessing — preventing hallucination on out-of-scope questions.
 
---
 
## Tech Stack
 
| Layer | Technology | Why |
|-------|-----------|-----|
| API | FastAPI | Async, auto-docs, type safety |
| Vector DB | PostgreSQL + pgvector | Cosine similarity search, no extra infrastructure |
| Embeddings | fastembed (BAAI/bge-small-en-v1.5) | Lightweight (~60MB), high quality, runs in container |
| LLM | Groq (openai/gpt-oss-20b) | Low latency inference |
| PDF parsing | pdfplumber | Reliable text extraction from PDFs |
| Frontend | Vanilla HTML/CSS/JS | Zero dependencies, instant load |
| Container | Docker Compose | Reproducible dev environment |
| CI | GitHub Actions | Automated testing on every push |
 
---
 
## Features
 
- **PDF upload** — drag in any PDF and start asking questions immediately
- **Source filtering** — answers are pulled only from your uploaded document, not mixed with other data
- **Deduplication** — re-uploading the same file replaces old chunks, no duplicates
- **Similarity guardrail** — refuses to answer when no relevant content is found
- **Chat-style UI** — clean dark interface with typing indicators and inline source citations
- **Multiple file support** — upload several PDFs and query across all of them
---
 
## Project Structure
 
```
doculens/
├── app/
│   ├── api/
│   │   ├── ask.py        # RAG pipeline: search → LLM → answer
│   │   └── search.py     # Vector search with pgvector + source filter
│   ├── ingest/
│   │   └── ingest.py     # PDF extraction, chunking, embedding, DB insert
│   └── main.py           # FastAPI app — /ask and /upload endpoints
├── frontend/
│   └── index.html        # Chat-style single-page UI
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
5. Upload a PDF using the UI and start asking questions
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
 
Response:
```json
{
  "answer": "The document mentions three projects: ...",
  "sources": ["resume.pdf"],
  "top_score": 0.42
}
```
 
**GET /health**
```json
{ "status": "ok", "service": "Doculens-api", "version": "0.1.0" }
```
 
---
 
## Key Design Decisions
 
**Why pgvector instead of a dedicated vector DB (Pinecone, Weaviate)?**
PostgreSQL with pgvector keeps the stack simple — one database handles both metadata and vectors. For a portfolio project and small-scale deployment, this avoids unnecessary infrastructure complexity.
 
**Why fastembed instead of sentence-transformers?**
fastembed is ~60MB vs ~500MB for sentence-transformers. In a Docker container this means significantly faster builds and less memory usage, with comparable embedding quality for English text.
 
**Why a similarity guardrail?**
Without it, the LLM would attempt to answer out-of-scope questions using irrelevant context, producing confident but wrong answers. The guardrail makes the system say "I don't know" instead of hallucinating.
 
**Why source filtering?**
When multiple PDFs are ingested, without filtering the search returns chunks from all documents. Filtering by `source` ensures answers come only from the document the user uploaded in that session.
 
**Why lazy Groq client initialization?**
Creating the client at module import time requires GROQ_API_KEY immediately. This broke CI where the key lives in secrets. Lazy init defers the check until an actual API call is made.
 
---
 
## Running Tests
 
```bash
pytest tests/ -v
```
 
CI runs automatically on every push to main and develop.
 
---
 
## Roadmap
 
- [ ] Streaming responses
- [ ] Markdown rendering in answers
- [ ] Per-session document management (list/delete uploaded files)
- [ ] Evaluation suite with golden Q&A dataset
- [ ] Multi-turn conversation with memory


