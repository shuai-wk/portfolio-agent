import re


def chunk_whole(text: str) -> list[str]:
    return [text]


def chunk_fixed(text: str, max_tokens: int = 512) -> list[str]:
    # Rough approximation for Chinese: one character is about 1.4 tokens.
    max_chars = int(max_tokens * 1.4)
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 2 > max_chars:
            chunks.append(current)
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}" if current else paragraph
    if current.strip():
        chunks.append(current)
    return chunks


def chunk_semantic(text: str) -> list[str]:
    parts = re.split(r"(?m)^(#{1,3} .*)$", text)
    sections: list[str] = []
    if parts[0].strip():
        sections.append(parts[0].strip())
    for index in range(1, len(parts), 2):
        heading = parts[index].strip()
        body = parts[index + 1].strip() if index + 1 < len(parts) else ""
        sections.append(f"{heading}\n{body}".strip())
    return [section for section in sections if section]

