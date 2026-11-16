import json
from collections.abc import Iterator

from fastapi.testclient import TestClient

from app.llm import LangfuseLLM
from app.main import app, get_agent


def parse_sse(body: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    for block in body.split("\n\n"):
        event_type = None
        data = None
        for line in block.splitlines():
            if line.startswith("event: "):
                event_type = line[len("event: ") :]
            elif line.startswith("data: "):
                data = json.loads(line[len("data: ") :])
        if event_type is not None and data is not None:
            events.append((event_type, data))
    return events


def test_ask_stream_emits_events(client) -> None:
    response = client.post("/api/ask/stream", json={"question": "你的技术栈是什么？"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = parse_sse(response.text)
    event_types = [event_type for event_type, _ in events]
    assert "step" in event_types
    assert "sources" in event_types
    assert "token" in event_types
    assert "done" in event_types
    assert "error" not in event_types

    done_events = [data for event_type, data in events if event_type == "done"]
    assert len(done_events) == 1
    assert "answer" in done_events[0]
    assert "sources" in done_events[0]


class FailingLLM:
    def invoke(self, prompt: str) -> str:
        raise RuntimeError("llm failed")

    def stream(self, prompt: str) -> Iterator[str]:
        raise RuntimeError("llm failed")


def test_ask_stream_emits_error(make_agent, fake_tracer) -> None:
    agent = make_agent(LangfuseLLM(FailingLLM(), fake_tracer))
    app.dependency_overrides[get_agent] = lambda: agent
    with TestClient(app) as client:
        response = client.post("/api/ask/stream", json={"question": "boom"})
    app.dependency_overrides.clear()

    events = parse_sse(response.text)
    assert events[-1][0] == "error"
    assert events[-1][1]["error"] == "llm failed"
