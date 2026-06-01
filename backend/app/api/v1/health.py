from fastapi import APIRouter

from app.core.config import settings
from app.db.health import check_database_connection


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
    }


@router.get("/readiness")
def readiness_check():
    database_ok = check_database_connection()

    return {
        "status": "ready" if database_ok else "degraded",
        "checks": {
            "api": "ok",
            "database": "ok" if database_ok else "failed",
            "ai_pipeline": "not_configured_yet",
        },
    }