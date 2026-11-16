from typing import Any, Protocol

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class DocumentRepo(Protocol):
    def search(self, vector: list[float], top_k: int = 5) -> list[dict[str, Any]]: ...


class PgVectorRepo:
    def __init__(self, dsn: str, table: str = "documents") -> None:
        self.dsn = dsn
        self.table = table

    def search(self, vector: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        vec = "[" + ",".join(str(value) for value in vector) + "]"
        table = sql.Identifier(self.table)
        query = sql.SQL(
            """
            SELECT id, content, metadata,
                   1 - (embedding <=> %s::vector) AS score
            FROM {}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """
        ).format(table)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.cursor() as cur:
            cur.execute(query, (vec, vec, top_k))
            return [
                {
                    "id": row["id"],
                    "content": row["content"],
                    "metadata": row["metadata"],
                    "score": float(row["score"]),
                }
                for row in cur.fetchall()
            ]


def ensure_schema(dsn: str, dim: int, recreate: bool = False) -> None:
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        if recreate:
            cur.execute("DROP TABLE IF EXISTS documents")
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS documents (
                id serial PRIMARY KEY,
                content text NOT NULL,
                embedding vector({dim}) NOT NULL,
                metadata jsonb NOT NULL DEFAULT '{{}}'::jsonb
            )
            """
        )


def reset_documents(dsn: str) -> None:
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE documents RESTART IDENTITY")


def insert_documents(dsn: str, docs: list[dict[str, Any]]) -> None:
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        for doc in docs:
            vec = "[" + ",".join(str(value) for value in doc["embedding"]) + "]"
            cur.execute(
                "INSERT INTO documents (content, embedding, metadata) VALUES (%s, %s::vector, %s)",
                (doc["content"], vec, Jsonb(doc["metadata"])),
            )

