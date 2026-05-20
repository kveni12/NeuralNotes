from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.services.database import ensure_schema

app = FastAPI(
    title="NeuralNotes Local API",
    description="Local-only Apple Notes semantic indexing and galaxy layout service.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5177", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    ensure_schema()


app.include_router(router, prefix="/api")
