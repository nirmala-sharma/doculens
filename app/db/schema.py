# schema.py - creates the table that stores document chunks + their vector embeddings

import os
import psycopg2

SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(384),
    page INTEGER
);

-- For databases created before page numbers were added
ALTER TABLE documents ADD COLUMN IF NOT EXISTS page INTEGER;
"""

def init_db():
    # Create the extension, table, and columns if they don't exist yet
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cursor = conn.cursor()
    cursor.execute(SCHEMA_SQL)
    conn.commit()
    cursor.close()
    conn.close()