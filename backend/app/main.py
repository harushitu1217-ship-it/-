from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import initialize_database, open_connection
from app.db.models import Base
from app.db.session import engine
from app.generator import generate_contents_with_ai
from app.modules.auth.routes import router as auth_router
from app.modules.catalog.routes import router as catalog_router
from app.modules.providers.routes import router as provider_router
from app.routes import create_router


def create_app(db_path: str | None = None, ai_generator=generate_contents_with_ai) -> FastAPI:
    app = FastAPI(title="明景内容运营助手")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def startup() -> None:
        Base.metadata.create_all(engine)
        with open_connection(db_path) as conn:
            initialize_database(conn)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    upload_dir = Path(__file__).resolve().parents[2] / "data" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

    app.include_router(create_router(db_path, ai_generator=ai_generator))
    app.include_router(auth_router)
    app.include_router(catalog_router)
    app.include_router(provider_router)
    return app


app = create_app()
