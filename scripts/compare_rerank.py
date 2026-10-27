from app.api.search import rerank_chunks,search_chunks

QUESTIONS = [
    "What is broadcasting in Numpy?",
    "What function creates an array filled with zeros?",
    "How is a NumPy array different from a Python list?",
]

for question in QUESTIONS:
    # Step 1: vector search gives 20 candidates, best first
    candidates = search_chunks(question, top_K=20, source_filter="numpy-user.pdf")

    # Remember each chunk's position in the vector results (1 = best)
    vector_rank = {r[1]:i for i,r in enumerate(candidates,1)}

    # Step 2: rerank and keep the best 5
    reranked = rerank_chunks(question, candidates, top_n=5)

    print("\n"+"="*90)
    print(f"QUESTION: {question}")
    print(f"{'NEW':>3} {'OLD':>3} {'SCORE':>7} CHUNK")
    for new_rank,r in enumerate(reranked,1):
     old_rank = vector_rank[r[1]]
     preview = r[1][:70].replace("\n"," ")
     print(f"{new_rank:>3} {old_rank:>3} {r[2]:>7.2f} {preview}")
