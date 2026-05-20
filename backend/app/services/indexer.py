from __future__ import annotations

from app.models.note import RawNote
from app.services.apple_notes import read_apple_notes
from app.services.clustering import layout_notes
from app.services.database import ensure_schema, save_edges, save_embeddings, update_layout, upsert_notes
from app.services.embeddings import content_hash, embed_notes
from app.services.redaction import redact_text
from app.services.seed import sample_notes


def run_incremental_index(use_sample_when_empty: bool = True) -> dict:
    ensure_schema()
    raw_notes: list[RawNote] = read_apple_notes()
    source = "apple-notes"
    if not raw_notes and use_sample_when_empty:
        raw_notes = sample_notes()
        source = "sample"
    raw_notes = [_redact_note(note) for note in raw_notes]

    hashes = {note.external_id: content_hash(note) for note in raw_notes}
    vectors, model_name = embed_notes(raw_notes)
    indexed, edges = layout_notes(raw_notes, vectors)

    upsert_notes(indexed, hashes)
    save_embeddings(vectors, model_name)
    update_layout(indexed)
    save_edges(edges)

    return {
        "notes": len(indexed),
        "edges": len(edges),
        "embedding_model": model_name,
        "source": source if raw_notes else "empty",
    }


def _redact_note(note: RawNote) -> RawNote:
    data = note.model_dump()
    data["title"] = redact_text(data["title"])
    data["body"] = redact_text(data["body"])
    return RawNote(**data)
