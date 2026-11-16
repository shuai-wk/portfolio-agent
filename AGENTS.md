# portfolio-agent

求职作品集 Agent：访客可浏览我的经历，并向内置 Agent 提问，Agent 基于真实资料回答。

## 目录边界

- `backend/`：Python 3.12 + FastAPI + LangGraph + PostgreSQL/pgvector。后端改动不跨出该目录，除非需要同步修改根级 `docker-compose.yml` 或对外协议。
- `frontend/`：Next.js 16 + TypeScript + Tailwind。前端只通过 BFF 调用后端，不直接持有密钥。
- `eval/`：离线评测脚本、Golden Set 与报告。
- `.codex/hooks.json` 与 `.codex/hooks/`：本仓库的 Codex hooks，禁止随手修改。
- 根级 `docker-compose.yml`：本地编排 postgres + backend + frontend。

## 精确验证命令

后端（与 CI 一致）：

```bash
cd backend
uv sync --extra dev
uv run --extra dev ruff check .
uv run --extra dev pytest -q
```

前端（与 CI 一致）：

```bash
cd frontend
pnpm install
pnpm lint
pnpm typecheck
```

整体运行：

```bash
cp .env.example .env
docker compose up --build
curl -s http://localhost:8000/health
docker compose down
```

## 完成标准

- `docker compose up` 拉起 postgres、backend、frontend 三个服务。
- backend 与 postgres 通过 healthcheck，frontend 依赖 backend 健康。
- `curl http://localhost:8000/health` 返回 `{"status":"ok"}`。
- 后端 `ruff check .` 与 `pytest -q` 通过；前端 `pnpm lint` 与 `pnpm typecheck` 通过。

## 代码约束

- 后端统一 Python 3.12，类型标注完整，ruff 默认规则必须通过。
- 新增端点先补测试；LLM、embedding、向量检索在测试中必须可注入 mock，禁止依赖真实 API。
- 不引入 LangChain AgentExecutor。
- 数据库 schema 变更走 `backend/scripts/seed.py` 或显式迁移，禁止手工改运行中的库。
- `.env` 不入库，密钥一律走环境变量。
