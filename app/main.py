from fastapi import FastAPI

app = FastAPI(
    title="Doculens",
    description="Citation-first RAG assistant for developer documentation",
    version="0.1.0"
)

@app.get("/health")
def health_check():
    return {"status": "ok",
            "service": "Doculens-api",
            "version": "0.1.0"
            }