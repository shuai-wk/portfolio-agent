import math
from collections import Counter
from collections.abc import Iterator
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from .db import DocumentRepo
from .embeddings import Embedder
from .llm import LLM


def _tokenize(text: str) -> list[str]:
    normalized = text.lower()
    return [
        *(normalized[index : index + 2] for index in range(len(normalized) - 1)),
        *(normalized[index : index + 3] for index in range(len(normalized) - 2)),
    ]


def _bm25_scores(
    query: str,
    docs: list[dict[str, Any]],
    k1: float = 1.5,
    b: float = 0.75,
) -> list[float]:
    query_tokens = set(_tokenize(query))
    if not query_tokens or not docs:
        return [0.0] * len(docs)
    token_counts = [Counter(_tokenize(doc["content"])) for doc in docs]
    lengths = [sum(counts.values()) for counts in token_counts]
    average = sum(lengths) / len(lengths) or 1.0
    doc_freq = {
        token: sum(1 for counts in token_counts if counts[token] > 0)
        for token in query_tokens
    }
    total = len(docs)
    scores: list[float] = []
    for counts, length in zip(token_counts, lengths, strict=True):
        score = 0.0
        for token in query_tokens:
            term_freq = counts[token]
            if term_freq == 0:
                continue
            idf = math.log(1 + (total - doc_freq[token] + 0.5) / (doc_freq[token] + 0.5))
            score += idf * term_freq * (k1 + 1) / (
                term_freq + k1 * (1 - b + b * length / average)
            )
        scores.append(score)
    return scores


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
        docs = self._retrieve(question)
        prompt = self._build_prompt(question, docs)
        answer = self.llm.invoke(prompt)
        sources = self._to_sources(docs)
        return {"retrieved": docs, "answer": answer, "sources": sources}

    def stream(self, question: str) -> Iterator[tuple[str, dict[str, Any]]]:
        try:
            yield ("step", {"step": "embedding", "message": "正在编码问题"})
            yield ("step", {"step": "retrieval", "message": "正在检索相关资料"})
            docs = self._retrieve(question)
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

    def _retrieve(self, question: str) -> list[dict[str, Any]]:
        vector = self.embedder.embed(question)
        candidates = self.repo.search(vector, top_k=30)
        bm25 = _bm25_scores(question, candidates)
        max_bm25 = max(bm25) or 1.0
        ranked = sorted(
            zip(candidates, bm25, strict=True),
            key=lambda item: 0.3 * float(item[0]["score"]) + 0.7 * (item[1] / max_bm25),
            reverse=True,
        )
        return [doc for doc, _ in ranked[:5]]

    @staticmethod
    def _build_prompt(question: str, docs: list[dict[str, Any]]) -> str:
        contexts = "\n\n".join(f"[{index}] {doc['content']}" for index, doc in enumerate(docs, 1))
        return f"Question: {question}\nContexts:\n{contexts}"

    @staticmethod
    def _to_sources(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        sources: list[dict[str, Any]] = []
        for doc in docs:
            source_id = str(doc["metadata"].get("source", doc["id"]))
            if source_id in seen:
                continue
            seen.add(source_id)
            sources.append(
                {
                    "id": doc["id"],
                    "content": doc["content"],
                    "metadata": doc["metadata"],
                    "score": doc["score"],
                }
            )
        return sources

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

