"""
Alerts API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_

from backend.core.database import get_db
from backend.models.alerts import Alert
from backend.models.cities import City

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/")
async def list_alerts(
    city_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """List recent alerts."""
    stmt = (
        select(Alert, City.name.label("city_name"))
        .join(City, Alert.city_id == City.id)
        .order_by(desc(Alert.created_at))
        .limit(limit)
    )
    if city_id:
        stmt = stmt.where(Alert.city_id == city_id)

    result = await db.execute(stmt)
    rows = result.all()

    return {
        "count": len(rows),
        "alerts": [
            {
                "id": alert.id,
                "city_id": alert.city_id,
                "city_name": city_name,
                "alert_type": alert.alert_type,
                "channel": alert.channel,
                "aqi_value": alert.aqi_value,
                "aqi_category": alert.aqi_category,
                "message": alert.message,
                "is_sent": alert.is_sent,
                "sent_at": alert.sent_at.isoformat() if alert.sent_at else None,
                "created_at": alert.created_at.isoformat(),
            }
            for alert, city_name in rows
        ],
    }
