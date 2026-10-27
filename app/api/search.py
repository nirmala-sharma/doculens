import os 
import psycopg2  # Python library that lets python code to talk to PostgreSQL database
from fastembed import TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder

# Load the same embedding model we used during ingestion
# It must be the same model so vectors are in the same "space"
model = TextEmbedding("BAAI/bge-small-en-v1.5", threads=2, enable_cpu_mem_arena=False)

# reranker : reads (question, chunk) paris together and scores relevance
reranker = TextCrossEncoder(model_name = "Xenova/ms-marco-MiniLM-L-6-v2",threads=2, enable_cpu_mem_arena=False)

def search_chunks(questions, top_K=20, source_filter=None):
    # Step 1: Convert the user's question into a vector(same way we converted the chunks)
    query_embedding = list(model.embed([questions]))[0].tolist()
    # Step 2: Connect to the database where our 452 chunks are stored
    # cursor is like a remote control to send SQL commands through the connection
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cursor = conn.cursor()

    # Step 3: Find the most similar chunks to our question
    # %s are safe placeholders - PostgreSQL fills them from the tuple below
    # embedding <-> %s::vector = distance between the stored chunk and question vector
    # (:: vector tells postgreSQL to treat our list of numbers as a vector type)
    # 1-distance = similarity score (we flip it because higher score = more similar is easier to read)
    # ORDER BY distance = most similar chunk comes first
    # LIMIT %s = only return top k results

    if source_filter:
        cursor.execute(
            """
            SELECT source, content, 1 - (embedding <-> %s::vector) AS score, page
            FROM documents
            WHERE source = %s
            ORDER BY embedding <-> %s::vector
            LIMIT %s
            """,
            (query_embedding, source_filter, query_embedding, int(top_K))
        )
    else:
        cursor.execute(
            """
            SELECT source, content, 1 - (embedding <-> %s::vector) AS score
            FROM documents
            ORDER BY embedding <-> %s::vector
            LIMIT %s
            """,
            (query_embedding, query_embedding, int(top_K))
        )
    # In plain english the query means like this : Go to the documents table. 
    # For every chunk stored there, calculate how 
    # similar it is to my question's vector.
    # Give me back the filename (source), the chunk text (content), and the similarity score. Sort them so the most similar chunk comes first. Only give me the top k.
    
    # Step 5: Close connection- its like closing a file after reading
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return results

def rerank_chunks(question, results, top_n=5):
    #results = list of (source, content, vector_score) from search_chunks
    if not results:
        return []

    # Pull out just the chunk texts
    documents = [r[1] for r in results]

    # Reranker gives one relevance score per chunk (higher = more relevant)
    rerank_scores = list(reranker.rerank(question, documents, batch_size = 8))

    # Pair each result with its rerank score
    scored = list(zip(results,rerank_scores))

    # Sort by rerank score, best first
    scored.sort(key=lambda x:x[1],reverse=True)

    # Keep top_n, return in the same (source, content, score, page) shape
    return [(r[0],r[1],float(s), r[3]) for r,s in scored[:top_n]]


    