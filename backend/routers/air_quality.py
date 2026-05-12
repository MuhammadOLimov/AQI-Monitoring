"""
Air Quality API endpoints.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from backend.core.database import get_db
from backend.schemas.schemas import AirQualityResponse, StatusResponse
from backend.services.air_quality_service import air_quality_service
from backend.services.city_service import city_service
from backend.utils.aqi_calculator import calculate_aqi, get_aqi_category, get_aqi_color

router = APIRouter(prefix="/air-quality", tags=["Air Quality"])


@router.get("/latest", response_model=List[dict])
async def get_latest_all_cities(db: AsyncSession = Depends(get_db)):
    """Get the latest air quality reading for all monitored cities."""
    data = await air_quality_service.get_latest_all_cities(db)
    result = []
    for item in data:
        city = item["city"]
        latest = item["latest"]
        entry = {
            "city": {
                "id": city.id,
                "name": city.name,
                "country": city.country,
                "country_code": city.country_code,
                "latitude": city.latitude,
                "longitude": city.longitude,
            },
            "latest": None,
        }
        if latest:
            entry["latest"] = {
                "id": latest.id,
                "timestamp": latest.timestamp.isoformat(),
                "aqi": latest.aqi,
                "aqi_category": latest.aqi_category,
                "aqi_color": get_aqi_color(latest.aqi),
                "pm2_5": latest.pm2_5,
                "pm10": latest.pm10,
                "co": latest.co,
                "no2": latest.no2,
                "so2": latest.so2,
                "o3": latest.o3,
                "nh3": latest.nh3,
            }
        result.append(entry)
    return result


@router.get("/city/{city_id}/latest")
async def get_city_latest(city_id: int, db: AsyncSession = Depends(get_db)):
    """Get latest air quality for a specific city."""
    city = await city_service.get_by_id(db, city_id)
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    record = await air_quality_service.get_latest_for_city(db, city_id)
    if not record:
        raise HTTPException(status_code=404, detail="No data available for this city")

    return {
        "city": {"id": city.id, "name": city.name, "country": city.country},
        "aqi": record.aqi,
        "aqi_category": record.aqi_category,
        "aqi_color": get_aqi_color(record.aqi),
        "timestamp": record.timestamp.isoformat(),
        "pollutants": {
            "pm2_5": record.pm2_5,
            "pm10": record.pm10,
            "co": record.co,
            "no2": record.no2,
            "so2": record.so2,
            "o3": record.o3,
            "nh3": record.nh3,
        },
    }


@router.get("/city/{city_id}/history")
async def get_city_history(
    city_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get historical air quality records for a city."""
    city = await city_service.get_by_id(db, city_id)
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    records = await air_quality_service.get_history(
        db, city_id, start_date, end_date, limit
    )

    return {
        "city": {"id": city.id, "name": city.name},
        "count": len(records),
        "records": [
            {
                "timestamp": r.timestamp.isoformat(),
                "aqi": r.aqi,
                "aqi_category": r.aqi_category,
                "aqi_color": get_aqi_color(r.aqi),
                "pm2_5": r.pm2_5,
                "pm10": r.pm10,
                "co": r.co,
                "no2": r.no2,
                "so2": r.so2,
                "o3": r.o3,
                "nh3": r.nh3,
            }
            for r in records
        ],
    }


@router.get("/city/{city_id}/analytics")
async def get_city_analytics(
    city_id: int,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics and statistics for a city."""
    city = await city_service.get_by_id(db, city_id)
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    analytics = await air_quality_service.get_analytics(db, city_id, start_date, end_date)
    records = analytics.pop("records", [])

    # Build time-series for each pollutant
    series = {
        "aqi": [], "pm2_5": [], "pm10": [], "co": [],
        "no2": [], "so2": [], "o3": [], "nh3": []
    }
    for r in records:
        ts = r.timestamp.isoformat()
        series["aqi"].append({"t": ts, "v": r.aqi})
        series["pm2_5"].append({"t": ts, "v": r.pm2_5})
        series["pm10"].append({"t": ts, "v": r.pm10})
        series["co"].append({"t": ts, "v": r.co})
        series["no2"].append({"t": ts, "v": r.no2})
        series["so2"].append({"t": ts, "v": r.so2})
        series["o3"].append({"t": ts, "v": r.o3})
        series["nh3"].append({"t": ts, "v": r.nh3})

    return {
        "city": {"id": city.id, "name": city.name, "country": city.country},
        **analytics,
        "series": series,
    }


@router.post("/city/{city_id}/fetch", response_model=StatusResponse)
async def trigger_fetch(
    city_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a data fetch for a specific city."""
    city = await city_service.get_by_id(db, city_id)
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    record = await air_quality_service.fetch_and_store(db, city)
    if not record:
        raise HTTPException(status_code=502, detail="Failed to fetch data from API")

    return StatusResponse(
        status="success",
        message=f"Data fetched for {city.name}",
        data={"aqi": record.aqi, "category": record.aqi_category},
    )


@router.post("/fetch-all", response_model=StatusResponse)
async def trigger_fetch_all(db: AsyncSession = Depends(get_db)):
    """Manually trigger data fetch for all monitored cities."""
    count = await air_quality_service.fetch_all_monitored_cities(db)
    return StatusResponse(
        status="success",
        message=f"Updated {count} cities",
        data={"updated": count},
    )


@router.get("/city/{city_id}/export/csv")
async def export_csv(
    city_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Export air quality data as CSV file."""
    city = await city_service.get_by_id(db, city_id)
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    csv_content = await air_quality_service.export_csv(db, city_id, start_date, end_date)

    filename = f"air_quality_{city.name.lower().replace(' ', '_')}.csv"
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
