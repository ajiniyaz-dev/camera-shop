import logging

from fastapi import FastAPI
from sqlalchemy.engine import Engine

from app.config import Settings, get_settings
from app.db import create_db_engine, create_session_factory
from app.health import router as health_router

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, engine: Engine | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

    app = FastAPI(
        title="HikVision Catalog API",
        debug=settings.debug,
        docs_url="/docs" if settings.debug else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.debug else None,
    )
    app.state.settings = settings
    app.state.engine = engine or create_db_engine(settings.database_url)
    app.state.session_factory = create_session_factory(app.state.engine)
    app.include_router(health_router)
    logger.info("API configured (env=%s, debug=%s)", settings.app_env, settings.debug)
    return app


app = create_app()
