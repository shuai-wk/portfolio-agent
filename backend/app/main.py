import json
from collections.abc import Iterator

from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse

from .agent import Agent
from .config import Settings, get_settings
from .db import DocumentRepo, PgVectorRepo
from .embeddings import Embedder, MockEmbedder
from .llm import LangfuseLLM, MockLLM, build_langfuse
from .schemas import AskRequest, AskResponse, Source

app = FastAPI(title="portfolio-agent backend")


def build_agent(settings: Settings) -> Agent:
    embedder: Embedder = MockEmbedder(settings.embedding_dim)
    repo: DocumentRepo = PgVectorRepo(settings.database_url)
    llm = LangfuseLLM(MockLLM(), build_langfuse(settings))
    return Agent(embedder=embedder, repo=repo, llm=llm)


_agent: Agent | None = None


def get_agent() -> Agent:
    global _agent
    if _agent is None:
        _agent = build_agent(get_settings())
    return _agent


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/agent")
def health_agent(agent: Agent = Depends(get_agent)) -> dict[str, list[str]]:
    return {"nodes": agent.node_names()}


@app.post("/api/ask", response_model=AskResponse)
def ask(request: AskRequest, agent: Agent = Depends(get_agent)) -> AskResponse:
    result = agent.invoke(request.question)
    return AskResponse(
        answer=result["answer"],
        sources=[Source(**source) for source in result["sources"]],
    )


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _stream_events(agent: Agent, question: str) -> Iterator[str]:
    for event, data in agent.stream(question):
        yield _sse(event, data)


@app.post("/api/ask/stream")
def ask_stream(request: AskRequest, agent: Agent = Depends(get_agent)) -> StreamingResponse:
    return StreamingResponse(
        _stream_events(agent, request.question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
