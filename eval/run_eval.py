import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db import PgVectorRepo  # noqa: E402

from embed import embed

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/portfolio"
)
TABLE = "eval_documents"
TOP_K = 5
GOLDEN_PATH = Path(__file__).resolve().parent / "golden_set.jsonl"
RESULTS_PATH = Path(__file__).resolve().parent / "results.json"


def load_golden() -> list[dict]:
    items: list[dict] = []
    with GOLDEN_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def source_id_of(row: dict) -> str:
    metadata = row.get("metadata") or {}
    return str(metadata.get("source_id", ""))


def evaluate(questions: list[dict]) -> dict:
    repo = PgVectorRepo(DATABASE_URL, table=TABLE)
    hit_at_1 = 0
    hit_at_3 = 0
    recall_sum = 0.0
    mrr_sum = 0.0
    details: list[dict] = []

    for item in questions:
        question = item["question"]
        expected = set(item["expected_source_ids"])
        vector = embed(question)
        rows = repo.search(vector, top_k=TOP_K)

        retrieved: list[str] = []
        seen: set[str] = set()
        for row in rows:
            source_id = source_id_of(row)
            if source_id and source_id not in seen:
                seen.add(source_id)
                retrieved.append(source_id)

        hit_1 = bool(retrieved) and retrieved[0] in expected
        hit_3 = any(source_id in expected for source_id in retrieved[:3])
        overlap = [source_id for source_id in retrieved[:TOP_K] if source_id in expected]
        recall = len(overlap) / len(expected) if expected else 0.0
        rank = next(
            (index + 1 for index, source_id in enumerate(retrieved) if source_id in expected),
            0,
        )
        mrr = 1.0 / rank if rank else 0.0

        hit_at_1 += int(hit_1)
        hit_at_3 += int(hit_3)
        recall_sum += recall
        mrr_sum += mrr
        details.append(
            {
                "question": question,
                "expected_source_ids": sorted(expected),
                "retrieved_source_ids": retrieved,
                "hit_at_1": hit_1,
                "hit_at_3": hit_3,
                "recall_at_5": recall,
                "mrr": mrr,
            }
        )

    count = len(questions) or 1
    return {
        "num_questions": len(questions),
        "hit_at_1": hit_at_1 / count,
        "hit_at_3": hit_at_3 / count,
        "recall_at_5": recall_sum / count,
        "mrr": mrr_sum / count,
        "details": details,
    }


def print_table(metrics: dict) -> None:
    print(f"metric     value  (n={metrics['num_questions']})")
    print("-------    -----")
    print(f"Hit@1      {metrics['hit_at_1']:.4f}")
    print(f"Hit@3      {metrics['hit_at_3']:.4f}")
    print(f"Recall@5   {metrics['recall_at_5']:.4f}")
    print(f"MRR        {metrics['mrr']:.4f}")


def main() -> None:
    questions = load_golden()
    metrics = evaluate(questions)
    print_table(metrics)
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else RESULTS_PATH
    output_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote results to {output_path}")


if __name__ == "__main__":
    main()

