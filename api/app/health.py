import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.db import check_database

logger = logging.getLogger(__name__)

router = APIRouter()

_NO_STORE = {"Cache-Control": "no-store"}


@router.get("/api/health")
def health(request: Request) -> JSONResponse:
    try:
        check_database(request.app.state.engine)
    except Exception as exc:
        logger.warning("Database health check failed (%s)", type(exc).__name__)
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "database": "unavailable"},
            headers=_NO_STORE,
        )
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "database": "ok"},
        headers=_NO_STORE,
    )
