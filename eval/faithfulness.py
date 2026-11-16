import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db import PgVectorRepo  # noqa: E402
from app.llm import LangfuseLLM, MockLLM  # noqa: E402

from embed import embed

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/portfolio"
)
TABLE = "eval_documents"
TOP_K = 3
SAMPLE_SIZE = 10
SEED = 42
GOLDEN_PATH = Path(__file__).resolve().parent / "golden_set.jsonl"
RESULTS_PATH = Path(__file__).resolve().parent / "faithfulness_results.json"


def load_golden() -> list[dict]:
    items: list[dict] = []
    with GOLDEN_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def build_prompt(question: str, rows: list[dict]) -> str:
    contexts = "\n\n".join(f"[{index}] {row['content']}" for index, row in enumerate(rows, 1))
    return f"Question: {question}\nContexts:\n{contexts}"


def ngrams(text: str, size: int = 2) -> set[str]:
    normalized = text.lower()
    return {normalized[index : index + size] for index in range(len(normalized) - size + 1)}


def faithfulness_score(answer: str, rows: list[dict]) -> float:
    context = " ".join(row["content"] for row in rows)
    answer_grams = ngrams(answer, 2)
    context_grams = ngrams(context, 2)
    if not answer_grams:
        return 1.0
    return len(answer_grams & context_grams) / len(answer_grams)


def verdict(score: float) -> str:
    if score >= 0.7:
        return "faithful"
    if score >= 0.4:
        return "partial"
    return "not_faithful"


def main() -> None:
    golden = load_golden()
    sampled = random.Random(SEED).sample(golden, min(SAMPLE_SIZE, len(golden)))
    repo = PgVectorRepo(DATABASE_URL, table=TABLE)
    llm = LangfuseLLM(MockLLM())

    items: list[dict] = []
    for item in sampled:
        question = item["question"]
        rows = repo.search(embed(question), top_k=TOP_K)
        answer = llm.invoke(build_prompt(question, rows))
        score = faithfulness_score(answer, rows)
        items.append(
            {
                "question": question,
                "answer": answer,
                "retrieved_source_ids": [row["metadata"].get("source_id") for row in rows],
                "faithfulness": score,
                "verdict": verdict(score),
            }
        )

    average = sum(row["faithfulness"] for row in items) / len(items)
    print("question                  faithfulness  verdict")
    print("----------------------    ------------  -----------")
    for row in items:
        question = row["question"][:20]
        print(f"{question:<24}  {row['faithfulness']:.4f}       {row['verdict']}")
    print(f"\nAverage faithfulness: {average:.4f}")

    result = {"sample_size": len(items), "avg_faithfulness": average, "items": items}
    RESULTS_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote results to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
