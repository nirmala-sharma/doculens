# schema.py - creates the table that stores document chunks + their vector embeddings

CREATE_DOCUMENTS_TABLE = """
CREATE EXTENSION IF NOT EXSTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(384)
);
"""