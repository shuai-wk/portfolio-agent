# frontend

Next.js 16 App Router + TypeScript + Tailwind。

## 常用命令

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm build
```

## 目录边界

- `app/page.tsx`：聊天界面（客户端组件，消费 SSE）。
- `app/api/ask/route.ts`：BFF，转发后端 SSE 并注入 API Key。
- `app/globals.css`：Tailwind 入口。

## 约定

- 后端地址走 `BACKEND_URL`，密钥走 `BACKEND_API_KEY`。
- SSE 由 `fetch + ReadableStream` 消费，逐字渲染 token，折叠展示 step。
