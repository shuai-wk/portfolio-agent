from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str


class Source(BaseModel):
    id: int
    content: str
    metadata: dict
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]

