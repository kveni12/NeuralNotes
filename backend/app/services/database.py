from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

import numpy as np

from app.models.note import IndexedNote

APP_DIR = Path.home() / "Library" / "Application Support" / "NeuralNotes"
DB_PATH = APP_DIR / "index.sqlite"


def connect() -> sqlite3.Connection:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_schema() -> None:
    with connect() as db:
        db.executescript(
            """
            create table if not exists notes (
              external_id text primary key,
              title text not null,
              body text not null,
              folder text,
              account text,
              tags_json text not null default '[]',
              attachments_json text not null default '[]',
              created_at text not null,
              updated_at text not null,
              content_hash text not null,
              cluster_id integer default -1,
              cluster_label text default 'Unclustered',
              x real default 0,
              y real default 0,
              radius real default 4,
              forgotten_months integer default 0,
              score real default 0.5
            );

            create table if not exists embeddings (
              external_id text primary key references notes(external_id) on delete cascade,
              vector_json text not null,
              model text not null,
              updated_at text not null
            );

            create table if not exists edges (
              source text not null,
              target text not null,
              similarity real not null,
              primary key (source, target)
            );

            create index if not exists idx_notes_updated_at on notes(updated_at);
            create index if not exists idx_notes_cluster on notes(cluster_id);
            """
        )


def upsert_notes(notes: Iterable[IndexedNote], content_hashes: dict[str, str]) -> None:
    with connect() as db:
        db.executemany(
            """
            insert into notes (
              external_id, title, body, folder, account, tags_json, attachments_json,
              created_at, updated_at, content_hash, cluster_id, cluster_label, x, y,
              radius, forgotten_months, score
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(external_id) do update set
              title=excluded.title,
              body=excluded.body,
              folder=excluded.folder,
              account=excluded.account,
              tags_json=excluded.tags_json,
              attachments_json=excluded.attachments_json,
              created_at=excluded.created_at,
              updated_at=excluded.updated_at,
              content_hash=excluded.content_hash,
              cluster_id=excluded.cluster_id,
              cluster_label=excluded.cluster_label,
              x=excluded.x,
              y=excluded.y,
              radius=excluded.radius,
              forgotten_months=excluded.forgotten_months,
              score=excluded.score
            """,
            [
                (
                    note.external_id,
                    note.title,
                    note.body,
                    note.folder,
                    note.account,
                    json.dumps(note.tags),
                    json.dumps(note.attachments),
                    note.created_at,
                    note.updated_at,
                    content_hashes[note.external_id],
                    note.cluster_id,
                    note.cluster_label,
                    note.x,
                    note.y,
                    note.radius,
                    note.forgotten_months,
                    note.score,
                )
                for note in notes
            ],
        )


def save_embeddings(vectors: dict[str, np.ndarray], model_name: str) -> None:
    with connect() as db:
        db.executemany(
            """
            insert into embeddings (external_id, vector_json, model, updated_at)
            values (?, ?, ?, datetime('now'))
            on conflict(external_id) do update set
              vector_json=excluded.vector_json,
              model=excluded.model,
              updated_at=excluded.updated_at
            """,
            [(note_id, json.dumps(vector.tolist()), model_name) for note_id, vector in vectors.items()],
        )


def save_edges(edges: list[tuple[str, str, float]]) -> None:
    with connect() as db:
        db.execute("delete from edges")
        db.executemany(
            "insert or replace into edges (source, target, similarity) values (?, ?, ?)",
            edges,
        )


def load_note_rows() -> list[sqlite3.Row]:
    with connect() as db:
        return list(db.execute("select * from notes order by updated_at desc"))


def load_embeddings() -> tuple[list[str], np.ndarray]:
    with connect() as db:
        rows = list(db.execute("select external_id, vector_json from embeddings"))
    if not rows:
        return [], np.zeros((0, 0))
    ids = [row["external_id"] for row in rows]
    matrix = np.array([json.loads(row["vector_json"]) for row in rows], dtype=np.float32)
    return ids, matrix


def update_layout(notes: list[IndexedNote]) -> None:
    with connect() as db:
        db.executemany(
            """
            update notes
            set cluster_id=?, cluster_label=?, x=?, y=?, radius=?, forgotten_months=?, score=?
            where external_id=?
            """,
            [
                (
                    note.cluster_id,
                    note.cluster_label,
                    note.x,
                    note.y,
                    note.radius,
                    note.forgotten_months,
                    note.score,
                    note.external_id,
                )
                for note in notes
            ],
        )


def get_index_stats() -> dict:
    with connect() as db:
        note_count = db.execute("select count(*) from notes").fetchone()[0]
        edge_count = db.execute("select count(*) from edges").fetchone()[0]
        cluster_count = db.execute("select count(distinct cluster_id) from notes").fetchone()[0]
    return {
        "notes": note_count,
        "edges": edge_count,
        "clusters": cluster_count,
        "cache": str(DB_PATH),
    }


def get_galaxy_payload() -> dict:
    rows = load_note_rows()
    if not rows:
        return {"notes": [], "edges": [], "clusters": []}

    notes = [
        {
            "id": row["external_id"],
            "title": row["title"],
            "body": row["body"],
            "folder": row["folder"],
            "tags": json.loads(row["tags_json"]),
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
            "clusterId": row["cluster_id"],
            "clusterLabel": row["cluster_label"],
            "x": row["x"],
            "y": row["y"],
            "radius": row["radius"],
            "forgottenMonths": row["forgotten_months"],
            "score": row["score"],
        }
        for row in rows
    ]

    clusters_by_id: dict[int, dict] = {}
    for note in notes:
        cluster = clusters_by_id.setdefault(
            note["clusterId"],
            {
                "id": note["clusterId"],
                "label": note["clusterLabel"],
                "color": "#7de3ff",
                "centroid": [0.0, 0.0],
                "count": 0,
            },
        )
        cluster["centroid"][0] += note["x"]
        cluster["centroid"][1] += note["y"]
        cluster["count"] += 1

    for cluster in clusters_by_id.values():
        cluster["centroid"][0] /= max(cluster["count"], 1)
        cluster["centroid"][1] /= max(cluster["count"], 1)

    with connect() as db:
        edges = [
            {"source": row["source"], "target": row["target"], "similarity": row["similarity"]}
            for row in db.execute("select source, target, similarity from edges order by similarity desc limit 2000")
        ]

    return {"notes": notes, "edges": edges, "clusters": list(clusters_by_id.values())}
