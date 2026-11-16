import os
from pathlib import Path

from app.config import get_settings
from app.db import ensure_schema, insert_documents
from app.embeddings import build_embedder

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = REPO_ROOT / "data"


def load_documents(data_dir: Path) -> list[dict]:
    documents_dir = data_dir / "documents"
    if not documents_dir.is_dir():
        return []
    documents: list[dict] = []
    for path in sorted(documents_dir.glob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if content:
            documents.append({"content": content, "metadata": {"source": path.name}})
    return documents


def main() -> None:
    settings = get_settings()
    data_dir = Path(os.environ.get("DATA_DIR", str(DEFAULT_DATA_DIR)))
    documents = load_documents(data_dir)
    if not documents:
        raise SystemExit(
            f"No markdown files found in {data_dir / 'documents'}. "
            "Copy data.example to data and add your own content."
        )
    embedder = build_embedder(settings)
    rows = [
        {
            "content": document["content"],
            "embedding": embedder.embed(document["content"]),
            "metadata": document["metadata"],
        }
        for document in documents
    ]
    dim = len(rows[0]["embedding"])
    ensure_schema(settings.database_url, dim, recreate=True)
    insert_documents(settings.database_url, rows)
    print(f"Seeded {len(rows)} documents from {data_dir} (embedding_dim={dim})")


if __name__ == "__main__":
    main()
