"""
Main FastAPI Application Entry Point.

Air Pollution Monitoring System
- Real-time air quality data collection
- AQI calculation and storage
- REST API with comprehensive documentation
- Scheduled background data fetching
"""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from loguru import logger

from backend.core.config import settings
from backend.core.logging import setup_logging
from backend.core.database import create_tables, AsyncSessionLocal
from backend.routers import cities, air_quality, alerts, health, admin
from backend.services.scheduler import create_scheduler
from backend.services.city_service import city_service


# ─── Application Lifecycle ─────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Handle startup and shutdown events."""
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.APP_ENV}")

    # Create database tables (Non-fatal startup)
    max_retries = 10
    retry_delay = 5
    db_initialized = False
    
    # Debug: log current DB host (masked)
    db_url = settings.DATABASE_URL
    if "@" in db_url:
        host_part = db_url.split("@")[-1]
        logger.info(f"Target Database Host: {host_part}")
    else:
        logger.warning(f"DATABASE_URL format is unusual: {db_url[:15]}...")

    async def init_db_task():
        nonlocal db_initialized
        for i in range(max_retries):
            try:
                await create_tables()
                async with AsyncSessionLocal() as db:
                    # Cleanup and seed
                    await city_service.cleanup_non_uz_cities(db)
                    await city_service.cleanup_duplicate_cities(db)
                    await city_service.ensure_default_cities(db)
                    await db.commit()
                
                logger.info("Database initialized and seeded successfully")
                db_initialized = True
                break
            except Exception as e:
                logger.warning(f"DB Init attempt {i+1}/{max_retries} failed: {e}")
                if i < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("Database initialization failed after all retries. App will run in degraded mode.")

    # Start DB initialization as a background task to not block server boot
    asyncio.create_task(init_db_task())

    # Start background scheduler
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("Background scheduler started")

    # Initial data fetch (non-blocking)
    async def initial_fetch():
        await asyncio.sleep(3)  # Short delay to let app fully start
        async with AsyncSessionLocal() as db:
            try:
                count = await air_quality_service.fetch_all_monitored_cities(db)
                await db.commit()
                logger.info(f"Initial fetch complete: {count} cities updated")
            except Exception as e:
                logger.warning(f"Initial fetch skipped: {e}")

    from backend.services.air_quality_service import air_quality_service
    asyncio.create_task(initial_fetch())

    yield  # Application runs here

    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info(f"{settings.APP_NAME} shutdown complete")


# ─── App Factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="""
## 🌍 Real-time Air Pollution Monitoring System

Monitor air quality across the globe with real-time AQI calculations.

### Features
- **Real-time data** from OpenWeatherMap Air Pollution API
- **AQI calculation** using US EPA methodology
- **Historical analytics** with trend analysis
- **Multi-city support** with interactive map
- **Email alerts** for high pollution levels
- **CSV export** for data analysis

### AQI Categories
| Range | Category | Color |
|-------|----------|-------|
| 0-50 | Good | 🟢 Green |
| 51-100 | Moderate | 🟡 Yellow |
| 101-150 | Unhealthy for Sensitive Groups | 🟠 Orange |
| 151-200 | Unhealthy | 🔴 Red |
| 201-300 | Very Unhealthy | 🟣 Purple |
| 301+ | Hazardous | ⬛ Maroon |
        """,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ─── Middleware ──────────────────────────────────────────────────────────
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.CORS_ALLOW_ALL else settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Static Files & Templates ────────────────────────────────────────────
    try:
        app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
    except Exception:
        logger.warning("Static files directory not found, skipping mount")

    # ─── API Routers ─────────────────────────────────────────────────────────
    prefix = settings.API_V1_PREFIX
    app.include_router(health.router)
    app.include_router(cities.router, prefix=prefix)
    app.include_router(air_quality.router, prefix=prefix)
    app.include_router(alerts.router, prefix=prefix)
    app.include_router(admin.router)

    # ─── Frontend Route ───────────────────────────────────────────────────────
    @app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
    async def dashboard(request: Request):
        try:
            templates = Jinja2Templates(directory="frontend/templates")
            return templates.TemplateResponse("dashboard.html", {"request": request})
        except Exception:
            return HTMLResponse("<h1>Dashboard not found. Run the full project setup.</h1>")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=1 if settings.RELOAD else settings.WORKERS,
        log_level="debug" if settings.DEBUG else "info",
    )
