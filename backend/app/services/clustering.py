from __future__ import annotations

import math
from collections import Counter, defaultdict
from datetime import datetime, timezone

from app.models.note import IndexedNote, RawNote


def layout_notes(notes: list[RawNote], vectors: dict[str, list[float]]) -> tuple[list[IndexedNote], list[tuple[str, str, float]]]:
    if not notes:
        return [], []

    ids = [note.external_id for note in notes if note.external_id in vectors]
    matrix = [vectors[note_id] for note_id in ids]
    labels = _cluster(matrix)
    positions = _project(matrix, labels)
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


def _cluster(matrix: list[list[float]]) -> list[int]:
    if len(matrix) < 5:
        return [0 for _ in matrix]

    k = max(2, min(9, int(math.sqrt(len(matrix) / 1.5))))
    step = max(1, len(matrix) // k)
    centroids = [matrix[min(index * step, len(matrix) - 1)][:] for index in range(k)]
    labels = [0 for _ in matrix]

    for _ in range(14):
        changed = False
        for index, vector in enumerate(matrix):
            label = max(range(k), key=lambda cluster: _cosine(vector, centroids[cluster]))
            if labels[index] != label:
                changed = True
                labels[index] = label
        buckets = [[] for _ in range(k)]
        for label, vector in zip(labels, matrix):
            buckets[label].append(vector)
        for index, bucket in enumerate(buckets):
            if bucket:
                centroids[index] = _normalize(_mean_vector(bucket))
        if not changed:
            break

    return labels


def _project(matrix: list[list[float]], labels: list[int]) -> list[tuple[float, float]]:
    if len(matrix) < 3:
        return [(0.0, 0.0) for _ in matrix]

    centered = _center(matrix)
    axis_a = _principal_axis(centered)
    residual = [_subtract_projection(vector, axis_a) for vector in centered]
    axis_b = _principal_axis(residual)
    raw = [(_dot(vector, axis_a), _dot(vector, axis_b)) for vector in centered]
    normalized = _normalize_points(raw)

    cluster_count = max(len(set(labels)), 1)
    separated = []
    for (x, y), label in zip(normalized, labels):
        angle = (2 * math.pi * label) / cluster_count
        separated.append(
            (
                max(-1, min(1, x * 0.72 + math.cos(angle) * 0.18)),
                max(-1, min(1, y * 0.72 + math.sin(angle) * 0.18)),
            )
        )
    return separated


def _cluster_names(ids: list[str], labels: list[int], notes: dict[str, RawNote]) -> dict[int, str]:
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


def _centrality_scores(matrix: list[list[float]]) -> list[float]:
    if len(matrix) == 1:
        return [1.0]
    scores = []
    for row in matrix:
        scores.append(sum(_cosine(row, other) for other in matrix) / len(matrix))
    return scores


def _build_edges(ids: list[str], matrix: list[list[float]]) -> list[tuple[str, str, float]]:
    edges: list[tuple[str, str, float]] = []
    for row in range(len(ids)):
        scored = []
        for col in range(len(ids)):
            if row == col:
                continue
            scored.append((col, _cosine(matrix[row], matrix[col])))
        for col, score in sorted(scored, key=lambda item: item[1], reverse=True)[:6]:
            if row < col and score >= 0.15:
                edges.append((ids[row], ids[col], score))
    edges.sort(key=lambda edge: edge[2], reverse=True)
    return edges[:5000]


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    return sum(a * b for a, b in zip(left, right))


def _center(matrix: list[list[float]]) -> list[list[float]]:
    mean = _mean_vector(matrix)
    return [[value - mean[index] for index, value in enumerate(vector)] for vector in matrix]


def _principal_axis(matrix: list[list[float]]) -> list[float]:
    dimensions = len(matrix[0])
    axis = _normalize([math.sin(index + 1) for index in range(dimensions)])
    for _ in range(18):
        projected = [0.0 for _ in range(dimensions)]
        for vector in matrix:
            weight = _dot(vector, axis)
            for index, value in enumerate(vector):
                projected[index] += value * weight
        axis = _normalize(projected)
    return axis


def _subtract_projection(vector: list[float], axis: list[float]) -> list[float]:
    weight = _dot(vector, axis)
    return [value - axis[index] * weight for index, value in enumerate(vector)]


def _mean_vector(vectors: list[list[float]]) -> list[float]:
    dimensions = len(vectors[0])
    return [sum(vector[index] for vector in vectors) / len(vectors) for index in range(dimensions)]


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _normalize_points(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    min_y = min(point[1] for point in points)
    max_y = max(point[1] for point in points)
    span_x = max(max_x - min_x, 1e-6)
    span_y = max(max_y - min_y, 1e-6)
    return [(((x - min_x) / span_x) * 2 - 1, ((y - min_y) / span_y) * 2 - 1) for x, y in points]


def _parse_date(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)
