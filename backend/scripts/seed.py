from app.config import get_settings
from app.db import ensure_schema, insert_documents, reset_documents
from app.embeddings import MockEmbedder

PLACEHOLDER_DOCS = [
    {
        "content": "我是一名后端工程师，熟练掌握 FastAPI、LangGraph 和 PostgreSQL。",
        "metadata": {"type": "experience"},
    },
    {
        "content": "我主导过基于 LangGraph 的 RAG 求职作品集 Agent 项目。",
        "metadata": {"type": "project"},
    },
    {
        "content": "我熟悉向量数据库 pgvector 和可观测性平台 Langfuse。",
        "metadata": {"type": "skill"},
    },
    {
        "content": "我使用 Python 3.12 和 TypeScript 进行全栈开发。",
        "metadata": {"type": "skill"},
    },
    {
        "content": "我关注代码质量，使用 ruff 和 pytest 做工程化保障。",
        "metadata": {"type": "habit"},
    },
]


def main() -> None:
    settings = get_settings()
    embedder = MockEmbedder(settings.embedding_dim)
    ensure_schema(settings.database_url, settings.embedding_dim)
    reset_documents(settings.database_url)
    docs = [
        {
            "content": doc["content"],
            "embedding": embedder.embed(doc["content"]),
            "metadata": doc["metadata"],
        }
        for doc in PLACEHOLDER_DOCS
    ]
    insert_documents(settings.database_url, docs)
    print(f"Seeded {len(docs)} documents")


if __name__ == "__main__":
    main()

