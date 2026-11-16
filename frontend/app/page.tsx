"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";

type Source = {
  id: number;
  content: string;
  metadata: Record<string, unknown>;
  score: number;
};

type UserMessage = {
  id: string;
  role: "user";
  content: string;
};

type AssistantMessage = {
  id: string;
  role: "assistant";
  content: string;
  steps: string[];
  sources: Source[];
  status: "streaming" | "done" | "error";
  error?: string;
};

type Message = UserMessage | AssistantMessage;

type ParsedEvent = {
  type: string;
  data: unknown;
};

function parseSseBlock(block: string): ParsedEvent | null {
  let type = "";
  const dataLines: string[] = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event: ")) {
      type = line.slice(7);
    } else if (line.startsWith("data: ")) {
      dataLines.push(line.slice(6));
    }
  }
  if (!type || dataLines.length === 0) {
    return null;
  }
  return { type, data: JSON.parse(dataLines.join("\n")) };
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  function updateAssistant(
    id: string,
    updater: (message: AssistantMessage) => AssistantMessage,
  ) {
    setMessages((current) =>
      current.map((message) =>
        message.id === id && message.role === "assistant" ? updater(message) : message,
      ),
    );
  }

  function appendStep(id: string, step: string) {
    updateAssistant(id, (message) => ({ ...message, steps: [...message.steps, step] }));
  }

  function appendToken(id: string, token: string) {
    updateAssistant(id, (message) => ({ ...message, content: message.content + token }));
  }

  function setSources(id: string, sources: Source[]) {
    updateAssistant(id, (message) => ({ ...message, sources }));
  }

  function finalize(id: string, answer: string, sources: Source[]) {
    updateAssistant(id, (message) => ({
      ...message,
      content: answer,
      sources,
      status: "done",
    }));
  }

  function setError(id: string, error: string) {
    updateAssistant(id, (message) => ({ ...message, status: "error", error }));
  }

  function handleEvent(event: ParsedEvent, assistantId: string) {
    switch (event.type) {
      case "step": {
        const data = event.data as { message?: string };
        if (data.message) {
          appendStep(assistantId, data.message);
        }
        break;
      }
      case "sources": {
        const data = event.data as { sources?: Source[] };
        setSources(assistantId, data.sources ?? []);
        break;
      }
      case "token": {
        const data = event.data as { token?: string };
        appendToken(assistantId, data.token ?? "");
        break;
      }
      case "done": {
        const data = event.data as { answer?: string; sources?: Source[] };
        finalize(assistantId, data.answer ?? "", data.sources ?? []);
        break;
      }
      case "error": {
        const data = event.data as { error?: string };
        setError(assistantId, data.error ?? "生成失败");
        break;
      }
      default:
        break;
    }
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = input.trim();
    if (!question || loading) {
      return;
    }
    setInput("");
    setLoading(true);

    const userMessage: UserMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
    };
    const assistantMessage: AssistantMessage = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: "",
      steps: [],
      sources: [],
      status: "streaming",
    };
    setMessages((current) => [...current, userMessage, assistantMessage]);

    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!response.ok || !response.body) {
        throw new Error(`请求失败: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }
        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split("\n\n");
        buffer = blocks.pop() ?? "";
        for (const block of blocks) {
          const event = parseSseBlock(block);
          if (event) {
            handleEvent(event, assistantMessage.id);
          }
        }
      }
      if (buffer.trim()) {
        const event = parseSseBlock(buffer);
        if (event) {
          handleEvent(event, assistantMessage.id);
        }
      }
    } catch (error) {
      setError(
        assistantMessage.id,
        error instanceof Error ? error.message : "请求失败",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex h-screen max-w-3xl flex-col px-4 py-6">
      <header className="border-b border-slate-200 pb-4">
        <h1 className="text-xl font-semibold text-slate-900">Portfolio Agent</h1>
        <p className="mt-1 text-sm text-slate-500">向我的作品集 Agent 提问</p>
      </header>

      <section className="flex-1 space-y-4 overflow-y-auto py-4">
        {messages.length === 0 && (
          <p className="py-12 text-center text-sm text-slate-400">
            输入一个问题开始对话。
          </p>
        )}
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
      </section>

      <form onSubmit={handleSubmit} className="flex gap-2 pt-4">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="例如：你的技术栈是什么？"
          className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          发送
        </button>
      </form>
    </main>
  );
}

function MessageBubble({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-lg bg-slate-900 px-3 py-2 text-sm text-white">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[92%] rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800">
        {message.steps.length > 0 && (
          <details className="mb-2 text-xs text-slate-500">
            <summary className="cursor-pointer select-none">步骤</summary>
            <ol className="mt-1 list-inside list-decimal space-y-0.5">
              {message.steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </details>
        )}

        <div className="prose prose-sm max-w-none">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
        {message.status === "streaming" && (
          <span className="ml-1 inline-block h-4 w-2 animate-pulse bg-slate-400 align-text-bottom" />
        )}
        {message.status === "error" && (
          <p className="mt-2 text-red-600">{message.error ?? "生成失败"}</p>
        )}

        {message.sources.length > 0 && (
          <details className="mt-2 text-xs text-slate-500">
            <summary className="cursor-pointer select-none">来源</summary>
            <ul className="mt-1 space-y-1">
              {message.sources.map((source) => (
                <li key={source.id} className="truncate">
                  {source.content}
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </div>
  );
}
