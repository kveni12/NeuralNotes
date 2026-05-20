from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone

import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics.pairwise import cosine_similarity

from app.models.note import IndexedNote, RawNote


def layout_notes(notes: list[RawNote], vectors: dict[str, np.ndarray]) -> tuple[list[IndexedNote], list[tuple[str, str, float]]]:
    if not notes:
        return [], []

    ids = [note.external_id for note in notes if note.external_id in vectors]
    matrix = np.array([vectors[note_id] for note_id in ids], dtype=np.float32)
    positions = _project(matrix)
    labels = _cluster(matrix)
    note_by_id = {note.external_id: note for note in notes}
    cluster_names = _cluster_names(ids, labels, note_by_id)
    scores = _centrality_scores(matrix)
    edges = _build_edges(ids, matrix)

    indexed = []
    now = datetime.now(timezone.utc)
    for index, note_id in enumerate(ids):
        raw = note_by_id[note_id]
        updated = _parse_date(raw.updated_at)
        forgotten_months = max(0, int((now - updated).days / 30))
        indexed.append(
            IndexedNote(
                **raw.model_dump(),
                cluster_id=int(labels[index]),
                cluster_label=cluster_names[int(labels[index])],
                x=float(positions[index][0]),
                y=float(positions[index][1]),
                radius=float(3.5 + min(6, len(raw.body) / 900)),
                forgotten_months=forgotten_months,
                score=float(scores[index]),
            )
        )

    return indexed, edges


def _project(matrix: np.ndarray) -> np.ndarray:
    if len(matrix) < 3:
        return np.zeros((len(matrix), 2), dtype=np.float32)
    try:
        import umap

        reducer = umap.UMAP(n_components=2, n_neighbors=min(18, len(matrix) - 1), min_dist=0.08, random_state=42)
        projected = reducer.fit_transform(matrix)
    except Exception:
        from sklearn.decomposition import PCA

        projected = PCA(n_components=2, random_state=42).fit_transform(matrix)
    return _normalize_positions(projected)


def _cluster(matrix: np.ndarray) -> np.ndarray:
    if len(matrix) < 6:
        return np.zeros(len(matrix), dtype=int)
    try:
        import hdbscan

        labels = hdbscan.HDBSCAN(min_cluster_size=max(4, min(16, len(matrix) // 12))).fit_predict(matrix)
        if len(set(labels)) > 1:
            return labels
    except Exception:
        pass
    clusters = max(2, min(9, int(np.sqrt(len(matrix)))))
    return MiniBatchKMeans(n_clusters=clusters, random_state=42, n_init="auto").fit_predict(matrix)


def _cluster_names(ids: list[str], labels: np.ndarray, notes: dict[str, RawNote]) -> dict[int, str]:
    stop = {"the", "and", "for", "with", "that", "this", "from", "into", "about", "notes", "note"}
    words_by_cluster: dict[int, Counter] = defaultdict(Counter)
    for note_id, label in zip(ids, labels):
        text = f"{notes[note_id].title} {' '.join(notes[note_id].tags)}".lower()
        words = [word.strip("#.,:;()[]") for word in text.split()]
        words_by_cluster[int(label)].update(word for word in words if len(word) > 3 and word not in stop)
    return {
        cluster: " ".join(word.title() for word, _ in counts.most_common(2)) or "Unclustered"
        for cluster, counts in words_by_cluster.items()
    }


def _centrality_scores(matrix: np.ndarray) -> np.ndarray:
    if len(matrix) == 1:
        return np.array([1.0])
    similarity = cosine_similarity(matrix)
    return similarity.mean(axis=1)


def _build_edges(ids: list[str], matrix: np.ndarray) -> list[tuple[str, str, float]]:
    if len(ids) < 2:
        return []
    similarity = cosine_similarity(matrix)
    edges: list[tuple[str, str, float]] = []
    for row in range(len(ids)):
        candidates = np.argsort(similarity[row])[-8:-1]
        for col in candidates:
            if row >= col:
                continue
            score = float(similarity[row][col])
            if score >= 0.55:
                edges.append((ids[row], ids[col], score))
    edges.sort(key=lambda edge: edge[2], reverse=True)
    return edges[:5000]


def _normalize_positions(points: np.ndarray) -> np.ndarray:
    minimum = points.min(axis=0)
    maximum = points.max(axis=0)
    span = np.maximum(maximum - minimum, 1e-6)
    normalized = ((points - minimum) / span) * 2 - 1
    return normalized.astype(np.float32)


def _parse_date(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)
