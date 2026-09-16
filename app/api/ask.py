import os
from groq import Groq
from dotenv import load_dotenv
from app.api.search import search_chunks

# Load environment variables from .env file
load_dotenv() 

# Create the Groq client - this is what we use to call the LLM
# It automatically picks up GROQ_API_KEY from environment
client = Groq(api_key=os.environ.get("GROQ_API_KEY")) 

# guadrail check
def get_answer(question):
    # Step 1: Search for the most relevant chunks from the database, search_chunks returns a list of tuples. Each tuple is (source, content, score)
    results = search_chunks(question)

    # Step 2: Guadrail- check if the top result is relevant enough
    # results[0]= first/best chunk, [2]=the score (index 0=source, 1=content, 2=score)
    top_score = results[0][2]
    if top_score < 0.3:
        return {
         "answer":"I couldn't find relevant information in the documentation.",
         "sources": [],
         "top_score": round(top_score, 3)
        }

    # Step 3: Build context from the top chunks i.e. we will build the prompt
    # We join all 5 chunks into one block of text for the LLM
    # Each chunk is labelled with its source file so LLM knows where it came from
    context = "\n\n".join(
         f"[Source:{r[0]}]\n{r[1]}" for r in results
     )

    # Collect unique source filenames for the citations in our response
    sources = list(set(r[0] for r in results))

    # Step 4: Build the prompt and call the LLM
    # System = instructions for how the LLM should behave (our guadrail prompt)
    # user = the actual question + the context chunks we retreived
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role":"system",
                "content":"You are a documentation assistant. Answer the user's question ONLY using the context provided. If the answer is not in the context, say 'I couldn't find this in the documentation.' Do Not use your own training knowlegde."

            },
            {
                "role":"user",
                "content":f"Context:\n{context}\n\nQuestion:{question}"
            }
        ]
    )

    # Step 5: Extract the answer text from the response and return everything
    answer = response.choices[0].message.content
    return {
        "answer":answer,
        "sources":sources,
        "top_score":round(top_score,3)
    }