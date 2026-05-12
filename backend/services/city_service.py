"""
City Service - CRUD operations and geocoding for cities.
Only Uzbekistan cities are supported.
"""
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from loguru import logger

from backend.models.cities import City
from backend.schemas.schemas import CityCreate, CityUpdate
from backend.services.openweather_service import openweather_service


# ─── Hardcoded Uzbekistan cities with precise coordinates ───────────────────────
# This ensures reliable seeding without depending on geocoding API accuracy
UZBEKISTAN_CITIES: Dict[str, dict] = {
    "Tashkent":     {"lat": 41.2995, "lon": 69.2401, "country": "Uzbekistan", "code": "UZ"},
    "Samarkand":    {"lat": 39.6542, "lon": 66.9597, "country": "Uzbekistan", "code": "UZ"},
    "Bukhara":      {"lat": 39.7747, "lon": 64.4286, "country": "Uzbekistan", "code": "UZ"},
    "Fergana":      {"lat": 40.3834, "lon": 71.7870, "country": "Uzbekistan", "code": "UZ"},
    "Andijan":      {"lat": 40.7821, "lon": 72.3442, "country": "Uzbekistan", "code": "UZ"},
    "Namangan":     {"lat": 40.9983, "lon": 71.6726, "country": "Uzbekistan", "code": "UZ"},
    "Navoiy":       {"lat": 40.1033, "lon": 65.3792, "country": "Uzbekistan", "code": "UZ"},
    "Urgench":      {"lat": 41.5533, "lon": 60.6317, "country": "Uzbekistan", "code": "UZ"},
    "Nukus":        {"lat": 42.4628, "lon": 59.6022, "country": "Uzbekistan", "code": "UZ"},
    "Qarshi":       {"lat": 38.8600, "lon": 65.7983, "country": "Uzbekistan", "code": "UZ"},
    "Termiz":       {"lat": 37.2241, "lon": 67.2783, "country": "Uzbekistan", "code": "UZ"},
    "Jizzax":       {"lat": 40.1158, "lon": 67.8422, "country": "Uzbekistan", "code": "UZ"},
    "Guliston":     {"lat": 40.4897, "lon": 68.7842, "country": "Uzbekistan", "code": "UZ"},
    "Olmaliq":      {"lat": 40.8447, "lon": 69.5986, "country": "Uzbekistan", "code": "UZ"},
    "Chirchiq":     {"lat": 41.4689, "lon": 69.5822, "country": "Uzbekistan", "code": "UZ"},
    "Angren":       {"lat": 41.0167, "lon": 70.1436, "country": "Uzbekistan", "code": "UZ"},
    "Bekobod":      {"lat": 40.2214, "lon": 69.2692, "country": "Uzbekistan", "code": "UZ"},
    "Margilan":     {"lat": 40.4714, "lon": 71.7144, "country": "Uzbekistan", "code": "UZ"},
    "Kokand":       {"lat": 40.5283, "lon": 70.9428, "country": "Uzbekistan", "code": "UZ"},
    "Denov":        {"lat": 38.2772, "lon": 67.8936, "country": "Uzbekistan", "code": "UZ"},
    "Shahrisabz":   {"lat": 39.0583, "lon": 66.8303, "country": "Uzbekistan", "code": "UZ"},
    "Zarafshon":    {"lat": 41.5744, "lon": 64.1853, "country": "Uzbekistan", "code": "UZ"},
    "Xiva":         {"lat": 41.3786, "lon": 60.3639, "country": "Uzbekistan", "code": "UZ"},
}


class CityService:

    async def get_all(self, db: AsyncSession, active_only: bool = True) -> List[City]:
        stmt = select(City).order_by(City.name)
        if active_only:
            stmt = stmt.where(City.is_active == True)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, db: AsyncSession, city_id: int) -> Optional[City]:
        result = await db.execute(select(City).where(City.id == city_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[City]:
        result = await db.execute(
            select(City).where(City.name.ilike(f"%{name}%")).limit(1)
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, city_data: CityCreate) -> City:
        city = City(**city_data.model_dump())
        db.add(city)
        await db.flush()
        await db.refresh(city)
        logger.info(f"Created city: {city.name}")
        return city

    async def update(
        self, db: AsyncSession, city_id: int, update_data: CityUpdate
    ) -> Optional[City]:
        city = await self.get_by_id(db, city_id)
        if not city:
            return None
        for field, value in update_data.model_dump(exclude_none=True).items():
            setattr(city, field, value)
        await db.flush()
        await db.refresh(city)
        return city

    async def delete(self, db: AsyncSession, city_id: int) -> bool:
        city = await self.get_by_id(db, city_id)
        if not city:
            return False
        await db.delete(city)
        return True

    async def search_and_add(
        self, db: AsyncSession, city_name: str
    ) -> Optional[City]:
        """Search for a city and add it — only Uzbekistan cities are accepted."""
        existing = await self.get_by_name(db, city_name)
        if existing:
            return existing

        # First check hardcoded Uzbekistan cities
        for name, info in UZBEKISTAN_CITIES.items():
            if name.lower() == city_name.lower().strip():
                city_data = CityCreate(
                    name=name,
                    country=info["country"],
                    country_code=info["code"],
                    latitude=info["lat"],
                    longitude=info["lon"],
                )
                return await self.create(db, city_data)

        # Fallback: try OpenWeatherMap geocoding, but only accept UZ results
        results = await openweather_service.geocode_city(city_name, limit=5)
        if not results:
            return None

        # Filter only Uzbekistan results
        uz_results = [r for r in results if r.get("country_code", "").upper() == "UZ"]
        if not uz_results:
            logger.warning(f"City '{city_name}' not found in Uzbekistan, skipping")
            return None

        r = uz_results[0]
        city_data = CityCreate(
            name=r["name"],
            country=r.get("country", "Uzbekistan"),
            country_code="UZ",
            latitude=r["latitude"],
            longitude=r["longitude"],
        )
        return await self.create(db, city_data)

    async def get_by_exact_name(self, db: AsyncSession, name: str) -> Optional[City]:
        """Get city by exact name match (case-insensitive)."""
        result = await db.execute(
            select(City).where(City.name.ilike(name)).limit(1)
        )
        return result.scalar_one_or_none()

    async def ensure_default_cities(self, db: AsyncSession) -> None:
        """Seed database with all Uzbekistan cities using hardcoded coordinates."""
        from backend.core.config import settings
        for city_name in settings.auto_fetch_cities_list:
            existing = await self.get_by_exact_name(db, city_name)
            if not existing:
                logger.info(f"Seeding city: {city_name}")
                # Use hardcoded data for reliable seeding
                if city_name in UZBEKISTAN_CITIES:
                    info = UZBEKISTAN_CITIES[city_name]
                    city_data = CityCreate(
                        name=city_name,
                        country=info["country"],
                        country_code=info["code"],
                        latitude=info["lat"],
                        longitude=info["lon"],
                    )
                    await self.create(db, city_data)
                else:
                    # Fallback to geocoding for any city not in hardcoded list
                    await self.search_and_add(db, city_name)

    async def cleanup_non_uz_cities(self, db: AsyncSession) -> int:
        """Remove all non-Uzbekistan cities and their related data from the database."""
        stmt = select(City).where(City.country_code != "UZ")
        result = await db.execute(stmt)
        non_uz_cities = result.scalars().all()

        count = 0
        for city in non_uz_cities:
            logger.info(f"Removing non-UZ city: {city.name} ({city.country})")
            await db.delete(city)
            count += 1

        if count > 0:
            logger.info(f"Cleaned up {count} non-Uzbekistan cities from database")
        return count

    async def cleanup_duplicate_cities(self, db: AsyncSession) -> int:
        """Remove duplicate cities keeping only one entry per unique coordinate pair."""
        stmt = select(City).where(City.country_code == "UZ").order_by(City.id)
        result = await db.execute(stmt)
        all_cities = result.scalars().all()

        seen_coords = {}  # (lat_rounded, lon_rounded) -> city
        seen_names = {}   # lowercase name -> city
        duplicates = []

        for city in all_cities:
            coord_key = (round(city.latitude, 2), round(city.longitude, 2))
            name_key = city.name.lower().strip()

            if coord_key in seen_coords or name_key in seen_names:
                duplicates.append(city)
                logger.info(f"Duplicate found: {city.name} (id={city.id})")
            else:
                seen_coords[coord_key] = city
                seen_names[name_key] = city

        for dup in duplicates:
            await db.delete(dup)

        if duplicates:
            logger.info(f"Removed {len(duplicates)} duplicate cities")
        return len(duplicates)


city_service = CityService()
