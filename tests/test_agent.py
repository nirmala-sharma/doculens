from types import SimpleNamespace
from app.api import agent
import json


def make_response(content=None, tool_calls=None):
    # Builds an object shaped like a real Groq response: response.choices[0].message
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])

def make_tool_call(query,call_id="call_1"):
    # Shaped like a real tool request from the LLM: search_documents(query)
    return SimpleNamespace(
        id = call_id,
        function = SimpleNamespace(
            name = "search_documents",
            arguments = json.dumps({"query":query})
        )
    )

class FakeClient:
    # Pretends t be a Groq client: returns scripted replies, one per call
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []               # remembers every request the agent sent
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)     #give back the next scripted reply


def test_answers_directly_when_no_tool_needed(monkeypatch):
    # The fake LLM answers right away, with no tool request
    client = FakeClient([make_response(content="Direct answer")])
    monkeypatch.setattr(agent,"get_client",lambda: client)      # lambda: client means “a function that returns client.”

    answer, passages = agent.run_agent("Hello?","a.pdf")

    assert answer == "Direct answer"   # the agent returned the LLM's answer
    assert passages == []     # no search, so no passages
    assert len(client.calls) == 1   # only one LLM call

def test_runs_search_then_answers(monkeypatch):
    # Fake LLM: first ask to search, then answer
    client = FakeClient([
        make_response(tool_calls=[make_tool_call("LogSignals")]),
        make_response(content="LogSignals is a log API [1]"),
    ])
    monkeypatch.setattr(agent,"get_client",lambda: client)

    # Fake search: records what was searched, instead of using the database
    searches = []
    def fake_search(query, source_filter, passages):
        searches.append((query, source_filter))
        passages.append({"source":source_filter,"page":1, "text":"fake passage"})
        return "[1] fake passage"
    monkeypatch.setattr(agent,"tool_search_documents",fake_search)

    answer, passages = agent.run_agent("What is LogSignals?","resume.pdf")

    assert searches == [("LogSignals","resume.pdf")] # search what the LLM asked, in our document
    assert answer == "LogSignals is a log API [1]"  # the final answer
    assert len(passages) == 1.  # the passage was collected for citations
    assert len(client.calls) == 2 # two LLM calls: one to search, one to answer

def test_step_limit_forces_final_answer(monkeypatch):
    # Fake LLM: asks to search in EVERY round, then gives a final answer when forced
    keep_searching = [
        make_response(tool_calls=[make_tool_call(f"try {i}", f"call_{i}")])
        for i in range(agent.MAX_TOOL_CALLS)
    ]
    client = FakeClient(keep_searching + [make_response(content="Final answer")])
    monkeypatch.setattr(agent,"get_client", lambda: client)

    searches = []
    def fake_search(query, source_filter, passages):
        searches.append((query,source_filter))
        passages.append({"source":source_filter,"page":1,"text":"fake passage"})
        return f"[{len(passages)}] fake passage"
    monkeypatch.setattr(agent,"tool_search_documents",fake_search)

    answer, passages = agent.run_agent("A hard question","a.pdf")
    assert answer == "Final answer" 
    assert len(client.calls) == agent.MAX_TOOL_CALLS + 1  # MAX_TOOL_CALLS searches(3), then one final answer
    assert client.calls[-1]["tool_choice"] == "none"  # the last call was forced to answer without tools





