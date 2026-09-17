from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.api.ask import get_answer

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

@app.post("/ask")
def ask(request: AskRequest):
    # Call get_answer with the question from the request body
    result = get_answer(request.question)
    return result