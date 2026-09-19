import os 
import psycopg2  # Python library that lets python code to talk to PostgreSQL database
from fastembed import TextEmbedding

# Load the same embedding model we used during ingestion
# It must be the same model so vectors are in the same "space"
model = TextEmbedding("BAAI/bge-small-en-v1.5")

def search_chunks(questions, top_K=5):
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
    # LIMIT %s = only return top 5 results

    cursor.execute(
        """
        SELECT source, content, 1 - (embedding <-> %s::vector) AS score
        from documents
        ORDER BY embedding <-> %s :: vector
        LIMIT %s
        """,
        (query_embedding, query_embedding, top_K)
    )
    # In plain english the query means like this : Go to the documents table. 
    # For every chunk stored there, calculate how 
    # similar it is to my question's vector.
    # Give me back the filename (source), the chunk text (content), and the similarity score. Sort them so the most similar chunk comes first. Only give me the top 5.
    
    # Step 5: Close connection- its like closing a file after reading
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return results
