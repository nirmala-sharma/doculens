from datetime import datetime
import json
import time
import requests

BASE_URL = "http://localhost:8000"  # address of API
SOURCE = "Nirmala_Sharma_Resume_SoftwareEngineering.pdf"        # name stored in the database
PDF_PATH = "Nirmala_Sharma_Resume_SoftwareEngineering.pdf"      # path to find the file on disk
AUTO_UPLOAD = True
USE_AGENT = True
RUN_LABEL = "agent" if USE_AGENT else "pipeline"       # file name 


# ( question, expected keywords, mode, should_answer)
# mode "any"= at least one keyword must appear in the answer
# model "all" = every keyword must appear (for broad questions)

TEST_CASES = [

# Rare names
("What did Nirmala contribute to Center Randomize?", ["pull request"], "any", True),
("What is Ghost charges?",["recurring", "subscription"], "any",True),
("What is LogSignals?", ["log"], "any", True),

# Exact numbers
("What accuracy did Digit Detective achieve?",["98.94"],"any",True),
("How many JUnit tests does LogSignals have?",["25"],"any",True),
("How many pytest tests does Ghost Charges have?",["37"],"any",True),

# Broad questions (need several facts)
("Which projects use FastAPI?", ["Ghost Charges","Citation"],"all",True),
("Which certifications does Nirmala have?",["IBM","Google"],"all",True),
("which programming languages does Nirmala know?",["Python","Java","SQL"],"all",True),

# Not in the resume (should be refused)
("What is Nirmala's salary expectation?",[],"any",False),
("What is Nirmala's favorite movie?",[],"any",False),
]


def upload_pdf():
    print(f"Uploading {SOURCE}...")
    with open(PDF_PATH, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/upload",
            files = {"file": (SOURCE, f, "application/pdf")},
            timeout = 300,
        )
    r.raise_for_status()

def ask(question):
    start = time.time()
    r = requests.post(f"{BASE_URL}/ask", json = {"question": question, "source": SOURCE, "use_agent": USE_AGENT},timeout=120)
    latency = round((time.time() - start)*1000)
    return r.json(), latency

def keywords_found(text, keywords, mode):
    text = text.lower()
    hits = [kw.lower() in text for kw in keywords]
    return all(hits) if mode == "all" else any(hits)

def run():
    if AUTO_UPLOAD:
        upload_pdf()

    answered_ok = 0     # correct answer (or correct refusal)
    grounded_ok = 0     # the expected facts are also in the cited passages

    results = []

    for i, (question, keywords, mode, should_answer) in enumerate(TEST_CASES, 1):
        resp, latency = ask(question)
        time.sleep(10)        # stay under the Groq free-tier rate limit

        answer = resp["answer"]
        citations = resp.get("citations",[])
        cited_text = " ".join(c.get("snippet","") for c in citations)

        if should_answer:
            passed = len(citations)>0 and keywords_found(answer,keywords, mode)
            grounded = passed and keywords_found(cited_text,keywords,mode)
        else:
            passed = len(citations) == 0         # refused
            grounded = passed

        answered_ok+=passed
        grounded_ok+=grounded
        print(f"{i:2}.{'✅' if passed else '❌'} answer {'✅' if grounded else '❌'} grounded "
              f"({latency} ms ) {question}")
        print(f"{answer[:150]}")

        results.append({
                "id":i,
                "question":question,
                "passed":bool(passed),
                "grounded":bool(grounded),
                "latency_ms":latency,
                "top_score":resp.get("top_score"),
                "answer":answer,
                "citations":[{"page":c.get("page"),"quote":c.get("quote")} for c in citations],
        })

    total = len(TEST_CASES)
    print(f"\nAnswered correctly:{answered_ok}/{total}")
    print(f"Grounded in citations:{grounded_ok}/{total}")

    summary = {
        "label": RUN_LABEL,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "answered": f"{answered_ok}/{total}",
        "grounded": f"{grounded_ok}/{total}",
        "results": results,
        
    }
    filename = f"evaluation_resume_{RUN_LABEL}.json"
    with open(filename,"w") as f:
        json.dump(summary,f,indent=2,ensure_ascii=False)
    print(f"Results saved to {filename}")
 

if __name__ == "__main__":
    run()



