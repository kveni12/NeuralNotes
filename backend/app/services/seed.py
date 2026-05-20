from datetime import datetime, timedelta, timezone

from app.models.note import RawNote


def sample_notes() -> list[RawNote]:
    now = datetime.now(timezone.utc)
    topics = [
        ("Designing calm software", "Product", ["design", "macos"], "Interfaces should feel quiet, fast, and respectful."),
        ("Vector search experiments", "Research", ["embeddings", "search"], "Compare cosine nearest neighbors against sparse retrieval."),
        ("Spring project ideas", "School", ["projects", "visualization"], "A galaxy map for notes could make old ideas easier to rediscover."),
        ("People map", "Personal", ["relationships"], "Track recurring collaborators and topics across meetings."),
        ("Local LLM summaries", "Research", ["llm", "privacy"], "Try small local models for weekly synthesis without cloud calls."),
        ("Garden planning", "Home", ["seasonal"], "Map sunlight, soil, and watering schedule over the next few months."),
        ("Thesis fragments", "School", ["writing"], "Bridge notes connect separate arguments and reveal structure."),
        ("Budget cleanup", "Admin", ["finance"], "Reduce subscriptions and categorize recurring expenses."),
        ("Conference notes", "Work", ["events"], "Ideas from hallway conversations are often hidden bridge nodes."),
        ("Memory resurfacing", "Product", ["ux", "memory"], "Old notes become valuable when connected to current work."),
    ]
    notes = []
    for index, (title, folder, tags, body) in enumerate(topics):
        notes.append(
            RawNote(
                external_id=f"sample-{index}",
                title=title,
                body=f"{body} {body} Related reflection number {index}.",
                folder=folder,
                tags=tags,
                created_at=(now - timedelta(days=80 + index * 19)).isoformat(),
                updated_at=(now - timedelta(days=index * 31)).isoformat(),
            )
        )
    return notes
