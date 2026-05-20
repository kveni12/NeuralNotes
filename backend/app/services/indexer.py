from __future__ import annotations

from app.models.note import RawNote
from app.services.apple_notes import read_apple_notes
from app.services.clustering import layout_notes
from app.services.database import ensure_schema, save_edges, save_embeddings, update_layout, upsert_notes
from app.services.embeddings import content_hash, embed_notes
from app.services.seed import sample_notes


def run_incremental_index(use_sample_when_empty: bool = True) -> dict:
    ensure_schema()
    raw_notes: list[RawNote] = read_apple_notes()
    if not raw_notes and use_sample_when_empty:
        raw_notes = sample_notes()

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
        "source": "apple-notes" if raw_notes else "empty",
    }
