"""
Cities API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.schemas.schemas import CityCreate, CityResponse, CityUpdate, StatusResponse
from backend.services.city_service import city_service
from backend.services.openweather_service import openweather_service

router = APIRouter(prefix="/cities", tags=["Cities"])


@router.get("/", response_model=List[CityResponse])
async def list_cities(
    active_only: bool = Query(True, description="Filter active cities only"),
    db: AsyncSession = Depends(get_db),
):
    """List all monitored cities."""
    cities = await city_service.get_all(db, active_only=active_only)
    return cities


@router.get("/{city_id}", response_model=CityResponse)
async def get_city(city_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific city by ID."""
    city = await city_service.get_by_id(db, city_id)
    if not city:
        raise HTTPException(status_code=404, detail=f"City {city_id} not found")
    return city


@router.post("/", response_model=CityResponse, status_code=201)
async def create_city(city_data: CityCreate, db: AsyncSession = Depends(get_db)):
    """Create a new monitored city."""
    city = await city_service.create(db, city_data)
    return city


@router.patch("/{city_id}", response_model=CityResponse)
async def update_city(
    city_id: int, update_data: CityUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a city."""
    city = await city_service.update(db, city_id, update_data)
    if not city:
        raise HTTPException(status_code=404, detail=f"City {city_id} not found")
    return city


@router.delete("/{city_id}", response_model=StatusResponse)
async def delete_city(city_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a city and all its data."""
    deleted = await city_service.delete(db, city_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"City {city_id} not found")
    return StatusResponse(status="success", message=f"City {city_id} deleted")


@router.get("/search/geocode")
async def search_cities(
    q: str = Query(..., min_length=2, description="City name to search"),
    db: AsyncSession = Depends(get_db),
):
    """Search cities via OpenWeatherMap geocoding API (Uzbekistan only)."""
    results = await openweather_service.geocode_city(q, limit=5, country_filter="UZ")
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"'{q}' O'zbekistonda topilmadi. Faqat O'zbekiston shaharlari qo'llab-quvvatlanadi."
        )
    return {"results": results, "count": len(results)}


@router.post("/search/add")
async def search_and_add_city(
    q: str = Query(..., min_length=2, description="City name to find and add"),
    db: AsyncSession = Depends(get_db),
):
    """Search for a city and add it to monitoring."""
    city = await city_service.search_and_add(db, q)
    if not city:
        raise HTTPException(
            status_code=404,
            detail=f"City '{q}' not found via geocoding API",
        )
    return {"status": "success", "city": city}
