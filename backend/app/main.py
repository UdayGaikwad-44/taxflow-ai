from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.utils.settings import settings
from app.routes import api_router


logger = logging.getLogger("taxflow")


def _mask_database_url(url: str) -> str:
    """
    Replace credentials in DB URL with *** for safe logging.
    Example: postgresql+asyncpg://user:pass@host/db → postgresql+asyncpg://***:***@host/db
    """
    try:
        scheme_idx = url.find("://")
        at_idx = url.find("@")
        if scheme_idx == -1 or at_idx == -1 or at_idx < scheme_idx:
            return url
        return f"{url[:scheme_idx+3]}***:***{url[at_idx:]}"
    except Exception:
        return url


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_url = os.getenv("DATABASE_URL") or settings.database_url
    logger.info("TaxFlow AI started")
    logger.info("DATABASE_URL=%s", _mask_database_url(db_url))
    logger.info("Database migrations are managed by Alembic — run 'alembic upgrade head' before starting.")
    yield
    logger.info("TaxFlow AI shutting down")


app = FastAPI(
    title="TaxFlow AI",
    version="2.0",
    description="AI-powered tax management for Indian freelancers, directors, and salaried professionals.",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "currency": settings.default_currency,
        "version": "2.0",
    }
