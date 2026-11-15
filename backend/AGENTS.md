# backend

Python 3.12 + FastAPI + LangGraph + PostgreSQL/pgvector。

## 常用命令

```bash
# 安装依赖（uv 管理 Python 3.12）
uv sync

# 启动开发服务
uv run uvicorn app.main:app --reload --port 8000

# 质量门禁
ruff check .
pytest -q

# 建表 + 灌占位数据（需要 postgres 已启动）
python -m scripts.seed
```

## 目录边界

- `app/`：FastAPI 应用、LangGraph agent，以及 DB/embedding/LLM 抽象。
- `tests/`：全部用 mock，不接触真实数据库或外部 API。
- `scripts/seed.py`：schema 初始化与占位文档。

## 约定

- LLM 调用必须经 `LangfuseLLM` 包装，走 Langfuse callback。
- embedder/repo/llm 必须可注入，测试替换为 mock。
- 新增端点先补测试。
