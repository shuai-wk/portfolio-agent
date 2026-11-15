# portfolio-agent

求职作品集 Agent：访客可浏览我的经历，并向内置 Agent 提问，Agent 基于真实资料回答。

## 目录边界

- `backend/`：Python 3.12 + FastAPI + LangGraph + PostgreSQL/pgvector。后端改动不跨出该目录，除非需要同步修改根级 `docker-compose.yml` 或对外协议。
- `frontend/`：Next.js（本阶段未启用，后续接入，先不建）。
- `eval/`：评测与数据（后续补充）。
- `.codex/hooks.json` 与 `.codex/hooks/`：本仓库的 Codex hooks，禁止随手修改。
- 根级 `docker-compose.yml`：本地编排 postgres + backend。

## 精确验证命令

后端质量门禁：

```bash
cd backend
ruff check .
pytest -q
```

整体运行与冒烟：

```bash
docker compose up --build -d
docker compose run --rm backend python -m scripts.seed
curl -s http://localhost:8000/health
curl -s http://localhost:8000/health/agent
curl -s -X POST http://localhost:8000/api/ask -H "Content-Type: application/json" -d "{\"question\":\"你的技术栈是什么？\"}"
docker compose down
```

## 完成标准

- `cd backend && ruff check . && pytest -q` 全部通过。
- `POST /api/ask` 对真实问题返回 `answer` 与 `sources`。
- `GET /health/agent` 返回 LangGraph 节点列表。
- 所有 LLM 调用经 Langfuse callback；未配置 key 时安全降级为 no-op。

## 代码约束

- 后端统一 Python 3.12，类型标注完整，ruff 默认规则必须通过。
- 新增端点先补测试；LLM、embedding、向量检索在测试中必须可注入 mock，禁止依赖真实 API。
- 不引入 LangChain AgentExecutor。
- 数据库 schema 变更走 `backend/scripts/seed.py` 或显式迁移，禁止手工改运行中的库。
- `.env` 不入库，密钥一律走环境变量。

