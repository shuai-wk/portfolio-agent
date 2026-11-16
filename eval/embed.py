import math
import zlib

DIM = 256


def embed(text: str, dim: int = DIM) -> list[float]:
    vector = [0.0] * dim
    normalized = text.lower()
    for index in range(len(normalized) - 1):
        gram = normalized[index : index + 2]
        vector[zlib.crc32(gram.encode("utf-8")) % dim] += 1.0
    for index in range(len(normalized) - 2):
        gram = normalized[index : index + 3]
        vector[zlib.crc32(gram.encode("utf-8")) % dim] += 1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]

