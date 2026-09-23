from  pathlib import Path
from fastembed import TextEmbedding
from dotenv import load_dotenv
import psycopg2
import os
import pdfplumber
import io


def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text
load_dotenv()  # Load environment variables from .env file

# Load the model once - loading it takes a few seconds
# so we do it once at the top, not inside every function
model = TextEmbedding("BAAI/bge-small-en-v1.5")

def chunk_text(text, chunk_size=100, overlap=20):
  # split the entire document into individual words
  # "How are you doing today" -> ["How", "are", "you", "doing", "today"]
    words = text.split()
    chunks = []   # This will hold all our chunks when we are done
    start = 0   # Start tracks which word we're curently at

   # Keep going until we've covered all words
    while start < len(words):
        # end is where this chunk stops
        end = start + chunk_size
        # Grab words from start to end and join them back into a string
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
       # Move forward - but go back 50 words(overlap)
       # So next chunk starts 50 words before where this one ended
        start += chunk_size - overlap

    return chunks

def read_file(filepath):
    # read the file and return its content as a string
    return Path(filepath).read_text(encoding='utf-8')

def embed_text(text):
    # Convert text into a list of 384 numbers
    embeddings = list(model.embed([text]))
    return embeddings[0].tolist()

def get_db_connection():
    # Read the database URL from environment variables and connect
    return psycopg2.connect(os.environ["DATABASE_URL"])

def store_chunk(cursor,source,chunk_index,content,embedding):
    # Insert one chunk and its embedding into the database
    cursor.execute(
        """
        INSERT INTO documents (source, chunk_index, content, embedding)
        VALUES (%s, %s, %s, %s)""",
        (source,chunk_index,content,embedding)
    )

def ingest_text(source: str, text: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents WHERE source = %s", (source,))  
    chunks = chunk_text(text)
    for i, chunk in enumerate(chunks):
        embedding = embed_text(chunk)
        store_chunk(cursor, source, i, chunk, embedding)
    conn.commit()
    cursor.close()
    conn.close()

def main():
    # Connect to the database once before processing anything
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create the table if it doesn't exist yet
    cursor.execute("""
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            source TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding vector(384)
        );
    """)

    # Find all markdown files in docs/raw folder
    docs_path = Path("docs/raw")
    md_files = list(docs_path.glob("**/*.md"))
    print(f"Found {len(md_files)} files")

    for filepath in md_files:
        source = str(filepath.relative_to(docs_path))
        text = read_file(filepath)
        chunks = chunk_text(text)
        print(f"Processing {source} with {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            embedding = embed_text(chunk)
            store_chunk(cursor, source, i, chunk, embedding)

    # Save all changes to database
    conn.commit()
    cursor.close()
    conn.close()
    print("Done!")

if __name__ == "__main__":
    main()