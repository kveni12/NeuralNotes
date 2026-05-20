from __future__ import annotations

import hashlib

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.preprocessing import normalize

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


def embed_notes(notes: list[RawNote]) -> tuple[dict[str, np.ndarray], str]:
    corpus = [f"{note.title}\n{note.body}\n{' '.join(note.tags)}" for note in notes]
    if not corpus:
        return {}, MODEL_NAME

    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(MODEL_NAME)
        matrix = model.encode(corpus, normalize_embeddings=True, show_progress_bar=False)
        return {note.external_id: matrix[index].astype(np.float32) for index, note in enumerate(notes)}, MODEL_NAME
    except Exception:
        vectorizer = HashingVectorizer(n_features=384, alternate_sign=False, norm=None)
        matrix = normalize(vectorizer.transform(corpus)).toarray().astype(np.float32)
        return {note.external_id: matrix[index] for index, note in enumerate(notes)}, "local-hashing-fallback"
