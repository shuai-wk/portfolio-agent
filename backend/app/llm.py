from typing import Any, Protocol

from langfuse import Langfuse

from .config import Settings


class LLM(Protocol):
    def invoke(self, prompt: str) -> str: ...


class Tracer(Protocol):
    def start_generation(self, *, name: str, input: Any) -> Any: ...


class MockLLM:
    def invoke(self, prompt: str) -> str:
        question = prompt.splitlines()[0].replace("Question:", "", 1).strip()
        return f"基于我的资料，对「{question}」的回答是：可以参考我的项目经历与技术栈。"


class LangfuseLLM:
    def __init__(self, llm: LLM, tracer: Tracer | None = None) -> None:
        self.llm = llm
        self.tracer = tracer

    def invoke(self, prompt: str) -> str:
        if self.tracer is None:
            return self.llm.invoke(prompt)
        generation = self.tracer.start_generation(name="llm", input={"prompt": prompt})
        try:
            output = self.llm.invoke(prompt)
            generation.update(output=output)
            generation.end()
            return output
        except Exception:
            generation.end(level="ERROR")
            raise


def build_langfuse(settings: Settings) -> Langfuse | None:
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None
    kwargs: dict[str, str] = {
        "public_key": settings.langfuse_public_key,
        "secret_key": settings.langfuse_secret_key,
    }
    if settings.langfuse_host:
        kwargs["host"] = settings.langfuse_host
    return Langfuse(**kwargs)

