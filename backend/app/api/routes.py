from fastapi import APIRouter, BackgroundTasks

from app.services.database import get_galaxy_payload, get_index_stats
from app.services.indexer import run_incremental_index

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"ok": True, "service": "neuralnotes-local"}


@router.get("/stats")
def stats() -> dict:
    return get_index_stats()


@router.get("/galaxy")
def galaxy() -> dict:
    return get_galaxy_payload()


@router.post("/sync")
def sync(background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(run_incremental_index)
    return {"started": True, "mode": "incremental"}
