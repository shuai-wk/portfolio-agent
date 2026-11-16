from collections.abc import Iterator
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from .db import DocumentRepo
from .embeddings import Embedder
from .llm import LLM


class AgentState(TypedDict, total=False):
    question: str
    retrieved: list[dict[str, Any]]
    answer: str
    sources: list[dict[str, Any]]


class Agent:
    def __init__(self, embedder: Embedder, repo: DocumentRepo, llm: LLM) -> None:
        self.embedder = embedder
        self.repo = repo
        self.llm = llm
        self.graph = self._build()

    def _run(self, state: AgentState) -> dict[str, Any]:
        question = state["question"]
        vector = self.embedder.embed(question)
        docs = self.repo.search(vector, top_k=5)
        prompt = self._build_prompt(question, docs)
        answer = self.llm.invoke(prompt)
        sources = self._to_sources(docs)
        return {"retrieved": docs, "answer": answer, "sources": sources}

    def stream(self, question: str) -> Iterator[tuple[str, dict[str, Any]]]:
        try:
            yield ("step", {"step": "embedding", "message": "正在编码问题"})
            vector = self.embedder.embed(question)
            yield ("step", {"step": "retrieval", "message": "正在检索相关资料"})
            docs = self.repo.search(vector, top_k=5)
            sources = self._to_sources(docs)
            yield ("sources", {"sources": sources})
            yield ("step", {"step": "generation", "message": "正在生成回答"})
            prompt = self._build_prompt(question, docs)
            chunks: list[str] = []
            for token in self.llm.stream(prompt):
                chunks.append(token)
                yield ("token", {"token": token})
            answer = "".join(chunks)
            yield ("done", {"answer": answer, "sources": sources})
        except Exception as exc:
            yield ("error", {"error": str(exc)})

    @staticmethod
    def _build_prompt(question: str, docs: list[dict[str, Any]]) -> str:
        contexts = "\n\n".join(f"[{index}] {doc['content']}" for index, doc in enumerate(docs, 1))
        return f"Question: {question}\nContexts:\n{contexts}"

    @staticmethod
    def _to_sources(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "id": doc["id"],
                "content": doc["content"],
                "metadata": doc["metadata"],
                "score": doc["score"],
            }
            for doc in docs
        ]

    def _build(self) -> Any:
        graph = StateGraph(AgentState)
        graph.add_node("agent", self._run)
        graph.add_edge(START, "agent")
        graph.add_edge("agent", END)
        return graph.compile()

    def invoke(self, question: str) -> dict[str, Any]:
        return self.graph.invoke({"question": question})

    def node_names(self) -> list[str]:
        graph = self.graph.get_graph()
        nodes = getattr(graph, "nodes", {})
        return [name for name in nodes if name not in {"__start__", "__end__"}]

