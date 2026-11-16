export const runtime = "nodejs";

export async function POST(request: Request) {
  const body = (await request.json()) as { question?: string };
  const question = body.question ?? "";
  const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";
  const apiKey = process.env.BACKEND_API_KEY ?? "";

  const upstream = await fetch(`${backendUrl}/api/ask/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
    },
    body: JSON.stringify({ question }),
  });

  const headers = {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    Connection: "keep-alive",
  };

  if (!upstream.ok || !upstream.body) {
    const message = `上游请求失败: ${upstream.status}`;
    const body = new ReadableStream({
      start(controller) {
        controller.enqueue(
          `event: error\ndata: ${JSON.stringify({ error: message })}\n\n`,
        );
        controller.close();
      },
    });
    return new Response(body, { status: 502, headers });
  }

  return new Response(upstream.body, { headers });
}
