from app.api.search import rerank_chunks

question = "What is Nirmala' python project experience?"

# Fake results in (source,content,score) shape

# Real answer is place LAST on purpose
fake_results = [
    ("resume.pdf", "Skills: Python, Java, SQL, Python libraries", 0.90, 1),
    ("resume.pdf", "Hobbies: reading, hiking, and travelling", 0.80, 2),
    ("resume.pdf", "Education: Bachelor's in Computer Science", 0.70, 1),
    ("resume.pdf", "Built DocuLens, a RAG app in Python using FastAPI and pgvector", 0.60, 1),
]

print("BEFORE:")
for r in fake_results:
    print(f"{r[2]:.2f} {r[1]}")

reranked = rerank_chunks(question, fake_results, top_n=4)

print("\nAFTER:")
for r in reranked:
    print(f"{r[2]:.2f} {r[1]}")