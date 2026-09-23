from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.api.ask import get_answer
from scripts.ingest import extract_text_from_pdf, ingest_text
from typing import Optional

app = FastAPI(
    title="Doculens",
    description="Citation-first RAG assistant for developer documentation",
    version="0.1.0"
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

@app.post("/ask")
def ask(request: AskRequest):
    # Call get_answer with the question from the request body
    result = get_answer(request.question, source_filter=request.source)
    return result

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    contents = await file.read()
    text = extract_text_from_pdf(contents)
    ingest_text(file.filename, text)
    return {"message": f"'{file.filename}' uploaded and ingested successfully."}