from pydantic import BaseModel, Field


class RawNote(BaseModel):
    external_id: str
    title: str
    body: str
    folder: str = "Notes"
    account: str = "Local"
    tags: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    attachments: list[dict] = Field(default_factory=list)


class IndexedNote(RawNote):
    cluster_id: int = -1
    cluster_label: str = "Unclustered"
    x: float = 0
    y: float = 0
    radius: float = 4
    forgotten_months: int = 0
    score: float = 0.5
