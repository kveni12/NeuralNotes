from dataclasses import dataclass, field


@dataclass
class RawNote:
    external_id: str
    title: str
    body: str
    folder: str = "Notes"
    account: str = "Local"
    tags: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    attachments: list[dict] = field(default_factory=list)

    def model_dump(self) -> dict:
        return {
            "external_id": self.external_id,
            "title": self.title,
            "body": self.body,
            "folder": self.folder,
            "account": self.account,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "attachments": self.attachments,
        }


@dataclass
class IndexedNote(RawNote):
    cluster_id: int = -1
    cluster_label: str = "Unclustered"
    x: float = 0
    y: float = 0
    radius: float = 4
    forgotten_months: int = 0
    score: float = 0.5
