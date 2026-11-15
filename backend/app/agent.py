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
        sources = [
            {
                "id": doc["id"],
                "content": doc["content"],
                "metadata": doc["metadata"],
                "score": doc["score"],
            }
            for doc in docs
        ]
        return {"retrieved": docs, "answer": answer, "sources": sources}

    @staticmethod
    def _build_prompt(question: str, docs: list[dict[str, Any]]) -> str:
        contexts = "\n\n".join(f"[{index}] {doc['content']}" for index, doc in enumerate(docs, 1))
        return f"Question: {question}\nContexts:\n{contexts}"

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

