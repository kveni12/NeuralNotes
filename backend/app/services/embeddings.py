from __future__ import annotations

import hashlib
import math

from app.models.note import RawNote

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def content_hash(note: RawNote) -> str:
    digest = hashlib.sha256()
    digest.update(note.title.encode("utf-8"))
    digest.update(b"\n")
    digest.update(note.body.encode("utf-8"))
    digest.update(b"\n")
    digest.update(note.updated_at.encode("utf-8"))
    return digest.hexdigest()


def embed_notes(notes: list[RawNote]) -> tuple[dict[str, list[float]], str]:
    corpus = [f"{note.title}\n{note.body}\n{' '.join(note.tags)}" for note in notes]
    if not corpus:
        return {}, MODEL_NAME

    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(MODEL_NAME)
        matrix = model.encode(corpus, normalize_embeddings=True, show_progress_bar=False)
        return {note.external_id: matrix[index].tolist() for index, note in enumerate(notes)}, MODEL_NAME
    except Exception:
        return {note.external_id: _hash_embed(text) for note, text in zip(notes, corpus)}, "stdlib-hashing-fallback"


def _hash_embed(text: str, dimensions: int = 192) -> list[float]:
    vector = [0.0] * dimensions
    for token in text.lower().split():
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=6).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]
