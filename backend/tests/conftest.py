from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.agent import Agent
from app.llm import LangfuseLLM
from app.main import app, get_agent


class FakeRepo:
    def __init__(self, docs: list[dict] | None = None) -> None:
        self.docs = docs or []

    def search(self, vector: list[float], top_k: int = 5) -> list[dict]:
        return self.docs[:top_k]


class FakeEmbedder:
    def __init__(self, dim: int = 4) -> None:
        self.dim = dim
        self.calls: list[str] = []

    def embed(self, text: str) -> list[float]:
        self.calls.append(text)
        return [0.1, 0.2, 0.3, 0.4][: self.dim]


class FakeLLM:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def invoke(self, prompt: str) -> str:
        self.calls.append(prompt)
        return "mock answer"

    def stream(self, prompt: str) -> Iterator[str]:
        self.calls.append(prompt)
        yield "mock"
        yield " answer"


class FakeGeneration:
    def __init__(self, name: str, input: dict) -> None:
        self.name = name
        self.input = input
        self.output: str | None = None
        self.level: str | None = None

    def update(self, **kwargs) -> None:
        self.output = kwargs.get("output")

    def end(self, **kwargs) -> None:
        self.level = kwargs.get("level")


class FakeTracer:
    def __init__(self) -> None:
        self.generations: list[FakeGeneration] = []

    def start_generation(self, *, name: str, input: dict) -> FakeGeneration:
        generation = FakeGeneration(name, input)
        self.generations.append(generation)
        return generation


@pytest.fixture
def fake_tracer() -> FakeTracer:
    return FakeTracer()


@pytest.fixture
def fake_repo() -> FakeRepo:
    return FakeRepo(
        [
            {"id": 1, "content": "doc one", "metadata": {"kind": "project"}, "score": 0.9},
            {"id": 2, "content": "doc two", "metadata": {}, "score": 0.8},
        ]
    )


@pytest.fixture
def make_agent(fake_repo: FakeRepo, fake_tracer: FakeTracer):
    def _make(llm) -> Agent:
        return Agent(embedder=FakeEmbedder(), repo=fake_repo, llm=llm)

    return _make


@pytest.fixture
def fake_agent(make_agent, fake_tracer: FakeTracer) -> Agent:
    return make_agent(LangfuseLLM(FakeLLM(), fake_tracer))


@pytest.fixture
def client(fake_agent: Agent) -> Iterator[TestClient]:
    app.dependency_overrides[get_agent] = lambda: fake_agent
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

