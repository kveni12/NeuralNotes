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
    labels = _cluster(notes)
    positions = _project(ids, labels)
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


def _cluster(notes: list[RawNote]) -> list[int]:
    groups: dict[str, int] = {}
    labels = []
    for note in notes:
        key = note.folder or (note.tags[0] if note.tags else "Notes")
        if key not in groups:
            groups[key] = len(groups)
        labels.append(groups[key])
    return labels


def _project(ids: list[str], labels: list[int]) -> list[tuple[float, float]]:
    counts = Counter(labels)
    offsets = defaultdict(int)
    cluster_count = max(len(counts), 1)
    positions = []
    for note_id, label in zip(ids, labels):
        cluster_angle = (2 * math.pi * label) / cluster_count
        cluster_radius = 0.58
        local_index = offsets[label]
        offsets[label] += 1
        local_angle = (2 * math.pi * local_index) / max(counts[label], 1)
        local_radius = 0.07 + 0.035 * math.sqrt(local_index + 1)
        stable_jitter = (sum(ord(char) for char in note_id) % 17) / 500
        x = math.cos(cluster_angle) * cluster_radius + math.cos(local_angle) * (local_radius + stable_jitter)
        y = math.sin(cluster_angle) * cluster_radius + math.sin(local_angle) * (local_radius + stable_jitter)
        positions.append((max(-1, min(1, x)), max(-1, min(1, y))))
    return positions


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


def _parse_date(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)
