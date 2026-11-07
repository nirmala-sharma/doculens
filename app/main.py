import os
import io
import pdfplumber
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.api.ask import get_answer, get_agent_answer
from scripts.ingest import extract_pages_from_pdf, ingest_pdf
from typing import Optional
from contextlib import asynccontextmanager
from app.db.schema import init_db

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
MAX_PAGES = int(os.getenv("MAX_PAGES", "300"))

@asynccontextmanager
async def lifespan(app):
    init_db()      # runs once when the app starts
    yield          # app runs here

app = FastAPI(
    title="Doculens",
    description="Citation-first RAG assistant for PDF documents",
    version="0.1.0",
    lifespan=lifespan
)

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/health")
def health_check():
    return {"status": "ok",
            "service": "Doculens-api",
            "version": "0.1.0"
            }



# Pydantic model defines the shape of the request body
# FastAPI uses this to automatically validate incoming JSON

class AskRequest(BaseModel):  # inherits from BaseModel — gets validation, type checking, auto JSON parsing
    question: str
    source: Optional[str] = None
    use_agent: bool = False   # True = agent, False = normal pipeline

@app.post("/ask")
def ask(request: AskRequest):
    if request.use_agent:
        return get_agent_answer(request.question, source_filter=request.source)
    return get_answer(request.question, source_filter=request.source)

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    contents = await file.read()

    # reject files that are too big
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException( status_code = 413, detail = f"File is too large. Maximum size is {MAX_UPLOAD_MB} MB.")

    # reject pdf with too many pages
    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            page_count = len(pdf.pages)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Could not read this PDF. Please make sure it is a valid PDF file.")

    if page_count > MAX_PAGES:
        raise HTTPException(status_code=413, detail=f"PDF has {page_count} pages. Maximum allowed is {MAX_PAGES} pages.")
    
    pages = extract_pages_from_pdf(contents)
    ingest_pdf(file.filename, pages)
    return {"message": f"'{file.filename}' uploaded and ingested successfully."}