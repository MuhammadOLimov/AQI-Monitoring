"""
Background scheduler using APScheduler.
Periodically fetches air quality data for all monitored cities.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from backend.core.config import settings
from backend.core.database import AsyncSessionLocal
from backend.services.air_quality_service import air_quality_service


async def _fetch_all_job() -> None:
    """Scheduled job: fetch data for all monitored cities."""
    logger.info("Scheduler: Starting bulk air quality fetch...")
    async with AsyncSessionLocal() as db:
        try:
            count = await air_quality_service.fetch_all_monitored_cities(db)
            await db.commit()
            logger.info(f"Scheduler: Updated {count} cities successfully")
        except Exception as e:
            await db.rollback()
            logger.error(f"Scheduler: Bulk fetch failed: {e}")


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _fetch_all_job,
        trigger=IntervalTrigger(seconds=settings.DATA_FETCH_INTERVAL),
        id="fetch_all_cities",
        name="Fetch all cities air quality",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=60,
    )
    logger.info(
        f"Scheduler configured: fetch every {settings.DATA_FETCH_INTERVAL}s "
        f"({settings.DATA_FETCH_INTERVAL // 60} minutes)"
    )
    return scheduler
