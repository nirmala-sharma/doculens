import app.api.ask as ask_module
from app.api.ask import validate_citations


CITATIONS = [
    {"id":1, "source":"a.pdf", "page": 3,"snippet":"text one"},
    {'id':2, "source":"a.pdf","page":9,"snippet":"text two"},
]

def test_removes_made_up_citation():
    answer, cits = validate_citations("NumPy is fast [1][5].", CITATIONS)
    assert "[5]" not in answer   # fake citation removed
    assert [c["id"] for c in cits ] == [1]    # only the used one returned

def test_keeps_all_when_none_cited():
    answer, cits = validate_citations("NumPy is fast.", CITATIONS)
    assert len(cits) == 2 

def test_converts_wide_brackets():
    answer, cits = validate_citations("NumPy is fast 【1】.", CITATIONS)
    assert "[1]" in answer
    assert "【" not in answer
    assert [c["id"] for c in cits] == [1]

def test_low_score_refuses_with_empty_citations(monkeypatch):
   # Regression test: the low-score guadrail used to crash with a NameError

   # Fake replacement for search_chunks: no database needed
   # Always returns one chunk with score 0.05( below 0.10 threshold)
   # Shape matches the real results: (source, content, score, page)
    def fake_search(question, top_K=20, source_filter=None):
        return [("a.pdf", "unrelated text", 0.05, 1)]

   # Inside ask.py, temporarily replace the real search_chunks with fake_search
   # pytest automatically restores the real one after this test
    monkeypatch.setattr(ask_module, "search_chunks",fake_search)

   # Call the REAL get_answer. It receives the low score and should refuse
   # (It stops at the guardrail, so Groq is never called)
    result = ask_module.get_answer("What is the weather?")

    assert result["citations"] == []     # refusal returns no citations
    assert result["sources"] == []       # and no sources
