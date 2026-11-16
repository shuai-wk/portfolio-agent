import os
import sys
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from chunk import chunk_fixed, chunk_semantic, chunk_whole
from embed import DIM, embed

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/portfolio"
)
TABLE = "eval_documents"

CORPUS = {
    "intro": "corpus/01_intro.md",
    "exp_a": "corpus/02_experience_a.md",
    "exp_b": "corpus/03_experience_b.md",
    "proj_rag": "corpus/04_project_rag_agent.md",
    "proj_realtime": "corpus/05_project_realtime.md",
    "proj_ecom": "corpus/06_project_ecommerce.md",
    "skills": "corpus/07_skills.md",
    "education": "corpus/08_education.md",
    "awards": "corpus/09_awards.md",
    "oss": "corpus/10_oss.md",
}

STRATEGIES = {
    "whole": chunk_whole,
    "fixed": chunk_fixed,
    "semantic": chunk_semantic,
}


def rebuild(strategy: str) -> int:
    chunk_fn = STRATEGIES[strategy]
    base = Path(__file__).resolve().parent
    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute(f"DROP TABLE IF EXISTS {TABLE}")
        cur.execute(
            f"CREATE TABLE {TABLE} (id serial PRIMARY KEY, content text NOT NULL, "
            f"embedding vector({DIM}) NOT NULL, metadata jsonb NOT NULL)"
        )

    total = 0
    with psycopg.connect(DATABASE_URL) as conn, conn.cursor() as cur:
        for source_id, relative_path in CORPUS.items():
            text = (base / relative_path).read_text(encoding="utf-8")
            for chunk_index, chunk_text in enumerate(chunk_fn(text)):
                metadata = {"source_id": source_id, "chunk_index": chunk_index}
                vec = "[" + ",".join(str(value) for value in embed(chunk_text)) + "]"
                cur.execute(
                    f"INSERT INTO {TABLE} (content, embedding, metadata) VALUES (%s, %s::vector, %s)",
                    (chunk_text, vec, Jsonb(metadata)),
                )
                total += 1
    return total


if __name__ == "__main__":
    strategy = sys.argv[1] if len(sys.argv) > 1 else "whole"
    count = rebuild(strategy)
    print(f"Rebuilt {TABLE} with strategy={strategy}: {count} chunks")

