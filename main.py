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

    # Create database tables with retries (for cloud environments)
    max_retries = 10
    retry_delay = 3
    
    # Debug: log current DB host (masked)
    db_parts = settings.DATABASE_URL.split("@")
    if len(db_parts) > 1:
        masked_url = f"postgresql+asyncpg://****:****@{db_parts[1]}"
        logger.info(f"Target Database: {masked_url}")
    else:
        logger.warning("DATABASE_URL format is unusual")

    for i in range(max_retries):
        try:
            await create_tables()
            logger.info("Database initialized successfully")
            break
        except Exception as e:
            if i == max_retries - 1:
                logger.error(f"Failed to initialize database after {max_retries} attempts: {e}")
                raise
            logger.warning(f"Database connection attempt {i+1}/{max_retries} failed. Retrying in {retry_delay}s... ({e})")
            await asyncio.sleep(retry_delay)

    # Cleanup non-Uzbekistan cities and seed defaults
    async with AsyncSessionLocal() as db:
        try:
            # Remove any non-Uzbekistan cities from previous configurations
            cleaned = await city_service.cleanup_non_uz_cities(db)
            if cleaned > 0:
                await db.commit()
                logger.info(f"Removed {cleaned} non-Uzbekistan cities")

            # Remove duplicate cities
            dupes = await city_service.cleanup_duplicate_cities(db)
            if dupes > 0:
                await db.commit()
                logger.info(f"Removed {dupes} duplicate cities")

            await city_service.ensure_default_cities(db)
            await db.commit()
            logger.info("Default Uzbekistan cities seeded")
        except Exception as e:
            await db.rollback()
            logger.warning(f"City seeding skipped: {e}")

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
