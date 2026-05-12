"""
Air Quality Service - core business logic for data fetching, saving, and analytics.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import csv
import io

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, text, Integer
from loguru import logger

from backend.models.cities import City
from backend.models.air_quality import AirQualityRecord
from backend.services.openweather_service import openweather_service
from backend.services.alert_service import alert_service


class AirQualityService:
    """Handles all air quality data operations."""

    async def fetch_and_store(
        self, db: AsyncSession, city: City
    ) -> Optional[AirQualityRecord]:
        """Fetch fresh data from API and persist to database."""
        logger.info(f"Fetching data for {city.name} ({city.latitude}, {city.longitude})")

        data = await openweather_service.get_current_air_pollution(
            city.latitude, city.longitude
        )
        if not data:
            logger.warning(f"No data returned for {city.name}")
            return None

        pollutants = data["pollutants"]
        record = AirQualityRecord(
            city_id=city.id,
            timestamp=data["timestamp"],
            aqi=data["aqi"],
            aqi_category=data["aqi_category"],
            pm2_5=pollutants.get("pm2_5"),
            pm10=pollutants.get("pm10"),
            co=pollutants.get("co"),
            no2=pollutants.get("no2"),
            so2=pollutants.get("so2"),
            o3=pollutants.get("o3"),
            nh3=pollutants.get("nh3"),
            no=pollutants.get("no"),
            nox=pollutants.get("nox"),
            ow_aqi=data.get("ow_aqi"),
        )
        db.add(record)
        await db.flush()
        await db.refresh(record)

        # Check and send alerts
        await alert_service.check_and_send_alert(db, city, record)

        logger.info(f"Stored AQI={record.aqi} ({record.aqi_category}) for {city.name}")
        return record

    async def get_latest_all_cities(
        self, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get the latest air quality record for every active city."""
        stmt = (
            select(City)
            .where(City.is_active == True, City.is_monitored == True)
            .order_by(City.name)
        )
        result = await db.execute(stmt)
        cities = result.scalars().all()

        output = []
        for city in cities:
            latest = await self.get_latest_for_city(db, city.id)
            output.append({"city": city, "latest": latest})
        return output

    async def get_latest_for_city(
        self, db: AsyncSession, city_id: int
    ) -> Optional[AirQualityRecord]:
        """Get latest record for a specific city."""
        stmt = (
            select(AirQualityRecord)
            .where(AirQualityRecord.city_id == city_id)
            .order_by(desc(AirQualityRecord.timestamp))
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_history(
        self,
        db: AsyncSession,
        city_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 200,
    ) -> List[AirQualityRecord]:
        """Get historical records with optional date range filter."""
        conditions = [AirQualityRecord.city_id == city_id]
        if start_date:
            conditions.append(AirQualityRecord.timestamp >= start_date)
        if end_date:
            conditions.append(AirQualityRecord.timestamp <= end_date)

        stmt = (
            select(AirQualityRecord)
            .where(and_(*conditions))
            .order_by(desc(AirQualityRecord.timestamp))
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_analytics(
        self, db: AsyncSession, city_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Compute analytics for a city over a time period."""
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            start_date = end_date - timedelta(days=7)

        conditions = [
            AirQualityRecord.city_id == city_id,
            AirQualityRecord.timestamp >= start_date,
            AirQualityRecord.timestamp <= end_date,
        ]

        # Aggregate stats
        stats_stmt = select(
            func.avg(AirQualityRecord.aqi).label("avg_aqi"),
            func.max(AirQualityRecord.aqi).label("max_aqi"),
            func.min(AirQualityRecord.aqi).label("min_aqi"),
            func.count(AirQualityRecord.id).label("total"),
            func.sum(
                (AirQualityRecord.aqi > 100).cast(Integer)
            ).label("unhealthy_hours"),
        ).where(and_(*conditions))

        result = await db.execute(stats_stmt)
        stats = result.one()

        # Time-series data (all records)
        ts_stmt = (
            select(AirQualityRecord)
            .where(and_(*conditions))
            .order_by(AirQualityRecord.timestamp)
        )
        ts_result = await db.execute(ts_stmt)
        records = ts_result.scalars().all()

        return {
            "avg_aqi": round(float(stats.avg_aqi or 0), 1),
            "max_aqi": stats.max_aqi or 0,
            "min_aqi": stats.min_aqi or 0,
            "total_records": stats.total or 0,
            "unhealthy_hours": stats.unhealthy_hours or 0,
            "records": records,
            "period_start": start_date,
            "period_end": end_date,
        }

    async def export_csv(
        self,
        db: AsyncSession,
        city_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> str:
        """Export historical data as CSV string."""
        records = await self.get_history(db, city_id, start_date, end_date, limit=10000)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Timestamp", "AQI", "Category",
            "PM2.5", "PM10", "CO", "NO2", "SO2", "O3", "NH3"
        ])
        for r in records:
            writer.writerow([
                r.timestamp.isoformat(),
                r.aqi, r.aqi_category,
                r.pm2_5, r.pm10, r.co, r.no2, r.so2, r.o3, r.nh3,
            ])
        return output.getvalue()

    async def fetch_all_monitored_cities(self, db: AsyncSession) -> int:
        """Fetch data for all monitored cities. Returns count of successful fetches."""
        stmt = select(City).where(City.is_active == True, City.is_monitored == True)
        result = await db.execute(stmt)
        cities = result.scalars().all()

        success = 0
        for city in cities:
            try:
                record = await self.fetch_and_store(db, city)
                if record:
                    success += 1
            except Exception as e:
                logger.error(f"Failed to fetch data for {city.name}: {e}")

        logger.info(f"Bulk fetch complete: {success}/{len(cities)} cities updated")
        return success


air_quality_service = AirQualityService()
