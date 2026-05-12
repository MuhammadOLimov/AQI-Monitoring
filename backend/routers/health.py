"""
Health check and system status endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db, check_db_connection
from backend.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """System health check."""
    db_ok = await check_db_connection()
    # Return 200 OK even if DB is down to prevent container restart loops
    # but include the actual status in the body
    return {
        "status": "healthy" if db_ok else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "database": "connected" if db_ok else "disconnected",
        "api_key_configured": bool(settings.OPENWEATHER_API_KEY),
        "email_enabled": settings.EMAIL_ALERTS_ENABLED,
    }


@router.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }
