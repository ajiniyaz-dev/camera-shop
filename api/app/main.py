import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.engine import Engine

from app.auth.rate_limit import LoginRateLimiter
from app.auth.router import router as auth_router
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
    app.state.login_rate_limiter = LoginRateLimiter(
        max_attempts=settings.login_rate_limit_max,
        window_seconds=settings.login_rate_limit_window_seconds,
        max_keys=settings.login_rate_limit_max_keys,
    )
    app.include_router(health_router)
    app.include_router(auth_router)

    @app.exception_handler(HTTPException)
    async def auth_http_errors(request: Request, exc: HTTPException) -> JSONResponse:
        headers = dict(exc.headers or {})
        if request.url.path.startswith("/api/auth"):
            headers["Cache-Control"] = "no-store"
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def hide_validation_input(request: Request, exc: RequestValidationError) -> JSONResponse:
        if request.url.path == "/api/auth/login":
            detail = "The login request is invalid."
        else:
            detail = "The request is invalid."
        return JSONResponse(
            status_code=422,
            content={"detail": detail},
            headers={"Cache-Control": "no-store"},
        )
    logger.info("API configured (env=%s, debug=%s)", settings.app_env, settings.debug)
    return app


app = create_app()
