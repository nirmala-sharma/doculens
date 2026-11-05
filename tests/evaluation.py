import requests
import time
import json

BASE_URL = "http://localhost:8000"
SOURCE = "numpy-user.pdf"      # name stored in the database
PDF_PATH = "numpy-user.pdf"    # path to find the file on disk
AUTO_UPLOAD = True
USE_AGENT = True               # True = agent, False = normal pipeline
RESULTS_FILE = "evaluation_results_agent.json" if USE_AGENT else "evaluation_results.json"

# Each tuple has 3 things:

# The question to ask
# Keywords we expect in the answer
# True = should answer, False = should refuse

TEST_CASES = [
    # ── Answerable questions (15) ──
    ("What is a NumPy array?",
     ["array", "ndarray", "homogeneous"], True),

    ("How is a NumPy array different from a Python list?",
     ["list", "array", "type"], True),

    ("What does the shape attribute of an array represent?",
     ["shape", "dimensions", "rows", "columns"], True),

    ("What is broadcasting in NumPy?",
     ["broadcast", "shape", "dimensions"], True),

    ("What function creates an array filled with zeros?",
     ["zeros", "np.zeros"], True),

    ("What is the dtype of a NumPy array?",
     ["dtype", "data type", "float", "int"], True),

    ("What does np.reshape do?",
     ["reshape", "shape", "dimensions"], True),

    ("What is a universal function (ufunc) in NumPy?",
     ["ufunc", "universal", "element-wise"], True),

    ("What is the difference between copy and view in NumPy?",
     ["copy", "view", "original"], True),

    ("How do you index a 2D NumPy array?",
     ["index", "row", "column"], True),

    ("What does np.linspace do?",
     ["linspace", "evenly", "spaced"], True),

    ("What is axis in NumPy operations?",
     ["axis", "row", "column", "dimension"], True),

    ("What does np.concatenate do?",
     ["concatenate", "join", "arrays"], True),

    ("What is the purpose of np.arange?",
     ["arange", "range", "values"], True),

    ("What does the transpose operation do to an array?",
     ["transpose", "axes", "rows", "columns"], True),

    # ── Refusal questions (5) ──
    ("What is the weather in New York today?",
     [], False),

    ("Who is the current president of the United States?",
     [], False),

    ("What is the capital of France?",
     [], False),

    ("How do I make pasta?",
     [], False),

    ("What is the stock price of Apple?",
     [], False),
]


def upload_pdf(pdf_path):
    print(f"Uploading PDF: {pdf_path}")
    with open(pdf_path, "rb") as f:
        r = requests.post(
    f"{BASE_URL}/upload",
    files={"file": ("numpy-user.pdf", f, "application/pdf")},
    timeout=300)
    r.raise_for_status()
    print(f"{r.json().get('message', 'Upload successful')}")
  
def ask(question):
    payload = {"question": question, "source": SOURCE, "use_agent": USE_AGENT}
    start = time.time()
    response = requests.post(f"{BASE_URL}/ask", json=payload,timeout=120)
    latency = round((time.time() - start) * 1000)
    return response.json(),latency

def check_answer(answer, keywords, should_answer, sources):
    answered = len(sources) > 0

    if should_answer:
        keybord_hit = any(kw.lower() in answer.lower() for kw in keywords) # Is any keyword from the list found in the answer?
        return answered and keybord_hit
    else:
        return not answered

def run_eval():
    if AUTO_UPLOAD:
        upload_pdf(PDF_PATH)

    passed_count = 0
    total_count = len(TEST_CASES)
    results = []

    for i, (question, keywords, should_answer) in enumerate(TEST_CASES, 1):  # loops with index starting at 1
        resp, latency = ask(question)
        time.sleep(30)       #  pauses the evaluation for 10 seconds after each question, before asking the next one. Stay under the Groq free-tier rate limit
        answer = resp["answer"]
        sources = resp["sources"]
        score = resp["top_score"]
        print(f"{i}. {tag} ({latency} ms) (score: {score}) {question}")

        passed = check_answer(answer, keywords, should_answer, sources)
        tag = "✅" if passed else "❌"
        print(f"   Answer: {answer[:150]}")

        if passed:
            passed_count += 1

        results.append({
            "id": i,
            "question": question,
            "passed": passed,
            "latency_ms": latency,
            "top_score": score,
            "answer": answer[:100]  # Store only the first 100 characters of the answer
        })

    print(f"\n --- Results ----")
    print(f"Passed: {passed_count}/{total_count}")
    print(f"Score: {round(passed_count / total_count * 100)}%")

    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=4)
    print(f"Results saved to {RESULTS_FILE}")

 
if __name__ == "__main__":
    run_eval()

    