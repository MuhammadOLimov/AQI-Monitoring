"""
OpenWeatherMap Air Pollution API integration.
Fetches real-time and historical air quality data.
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.core.config import settings
from backend.utils.aqi_calculator import calculate_aqi, AQIResult


class OpenWeatherService:
    """Async client for OpenWeatherMap APIs."""

    BASE_URL = "http://api.openweathermap.org/data/2.5"
    GEO_URL = "http://api.openweathermap.org/geo/1.0"

    def __init__(self) -> None:
        self.api_key = settings.OPENWEATHER_API_KEY
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _get(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make authenticated GET request with retry logic."""
        client = await self._get_client()
        params["appid"] = self.api_key
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def get_current_air_pollution(
        self, lat: float, lon: float
    ) -> Optional[Dict[str, Any]]:
        """Fetch current air pollution data for a coordinate."""
        try:
            data = await self._get(
                f"{self.BASE_URL}/air_pollution",
                {"lat": lat, "lon": lon},
            )
            return self._parse_pollution_response(data)
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching air pollution [{lat},{lon}]: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error fetching air pollution [{lat},{lon}]: {e}")
            return None

    async def get_historical_air_pollution(
        self, lat: float, lon: float, start: datetime, end: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch historical air pollution data."""
        try:
            start_ts = int(start.timestamp())
            end_ts = int(end.timestamp())
            data = await self._get(
                f"{self.BASE_URL}/air_pollution/history",
                {"lat": lat, "lon": lon, "start": start_ts, "end": end_ts},
            )
            results = []
            for item in data.get("list", []):
                parsed = self._parse_single_item(item)
                if parsed:
                    results.append(parsed)
            return results
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return []

    async def geocode_city(
        self, city_name: str, limit: int = 5, country_filter: str = "UZ"
    ) -> List[Dict[str, Any]]:
        """Geocode a city name to coordinates using OpenWeatherMap Geocoding API.
        
        Args:
            city_name: City name to search for.
            limit: Maximum number of results.
            country_filter: If set, only return results from this country code.
                          Set to None to return all results.
        """
        try:
            # Append country code to query for better results
            query = f"{city_name},{country_filter}" if country_filter else city_name
            data = await self._get(
                f"{self.GEO_URL}/direct",
                {"q": query, "limit": limit},
            )
            results = []
            for item in data:
                item_country = item.get("country", "")
                # Filter by country if specified
                if country_filter and item_country.upper() != country_filter.upper():
                    continue
                results.append({
                    "name": item.get("name", ""),
                    "country": item_country,
                    "country_code": item_country,
                    "state": item.get("state", ""),
                    "latitude": item.get("lat", 0),
                    "longitude": item.get("lon", 0),
                })
            return results
        except Exception as e:
            logger.error(f"Geocoding error for '{city_name}': {e}")
            return []

    def _parse_pollution_response(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse OpenWeatherMap /air_pollution response."""
        items = data.get("list", [])
        if not items:
            return None
        return self._parse_single_item(items[0])

    def _parse_single_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single air_pollution list item."""
        try:
            components = item.get("components", {})
            ow_aqi = item.get("main", {}).get("aqi")
            ts = item.get("dt", 0)
            timestamp = datetime.fromtimestamp(ts, tz=timezone.utc)

            pm2_5 = components.get("pm2_5")
            pm10 = components.get("pm10")
            co = components.get("co")
            no2 = components.get("no2")
            so2 = components.get("so2")
            o3 = components.get("o3")
            nh3 = components.get("nh3")
            no = components.get("no")
            nox = components.get("no_x")  # Some versions use no_x

            # Calculate AQI
            result: AQIResult = calculate_aqi(
                pm2_5=pm2_5,
                pm10=pm10,
                co=co,
                no2=no2,
                so2=so2,
                o3=o3,
                nh3=nh3,
            )

            return {
                "timestamp": timestamp,
                "aqi": result.aqi,
                "aqi_category": result.category,
                "dominant_pollutant": result.dominant_pollutant,
                "aqi_color": result.color,
                "ow_aqi": ow_aqi,
                "pollutants": {
                    "pm2_5": pm2_5,
                    "pm10": pm10,
                    "co": co,
                    "no2": no2,
                    "so2": so2,
                    "o3": o3,
                    "nh3": nh3,
                    "no": no,
                    "nox": nox,
                },
                "sub_indices": result.sub_indices,
                "health_message": result.health_message,
            }
        except Exception as e:
            logger.error(f"Error parsing pollution item: {e}")
            return None


# Singleton instance
openweather_service = OpenWeatherService()
