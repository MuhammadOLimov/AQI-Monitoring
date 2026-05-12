"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# ─── City Schemas ─────────────────────────────────────────────────────────────

class CityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=1, max_length=100)
    country_code: str = Field(..., min_length=2, max_length=10)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timezone: str = Field(default="UTC")


class CityCreate(CityBase):
    pass


class CityUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    is_monitored: Optional[bool] = None


class CityResponse(CityBase):
    id: int
    is_active: bool
    is_monitored: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Air Quality Schemas ───────────────────────────────────────────────────────

class PollutantsData(BaseModel):
    pm2_5: Optional[float] = Field(None, ge=0, description="PM2.5 μg/m³")
    pm10: Optional[float] = Field(None, ge=0, description="PM10 μg/m³")
    co: Optional[float] = Field(None, ge=0, description="CO μg/m³")
    no2: Optional[float] = Field(None, ge=0, description="NO2 μg/m³")
    so2: Optional[float] = Field(None, ge=0, description="SO2 μg/m³")
    o3: Optional[float] = Field(None, ge=0, description="O3 μg/m³")
    nh3: Optional[float] = Field(None, ge=0, description="NH3 μg/m³")
    no: Optional[float] = Field(None, ge=0, description="NO μg/m³")
    nox: Optional[float] = Field(None, ge=0, description="NOx μg/m³")


class AirQualityCreate(BaseModel):
    city_id: int
    timestamp: datetime
    aqi: int = Field(..., ge=0)
    aqi_category: str
    pollutants: PollutantsData
    ow_aqi: Optional[int] = Field(None, ge=1, le=5)


class AirQualityResponse(BaseModel):
    id: int
    city_id: int
    city_name: Optional[str] = None
    timestamp: datetime
    aqi: int
    aqi_category: str
    pm2_5: Optional[float] = None
    pm10: Optional[float] = None
    co: Optional[float] = None
    no2: Optional[float] = None
    so2: Optional[float] = None
    o3: Optional[float] = None
    nh3: Optional[float] = None
    no: Optional[float] = None
    nox: Optional[float] = None
    ow_aqi: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AirQualityLatest(BaseModel):
    city: CityResponse
    latest_record: Optional[AirQualityResponse] = None
    aqi_color: str = "#gray"
    aqi_label: str = "N/A"


# ─── Analytics Schemas ─────────────────────────────────────────────────────────

class AnalyticsQuery(BaseModel):
    city_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    interval: str = Field(default="hourly", pattern="^(hourly|daily|weekly)$")


class TimeSeriesPoint(BaseModel):
    timestamp: datetime
    value: Optional[float]


class PollutantTimeSeries(BaseModel):
    pollutant: str
    unit: str
    data: List[TimeSeriesPoint]


class AnalyticsResponse(BaseModel):
    city: CityResponse
    period_start: datetime
    period_end: datetime
    avg_aqi: Optional[float]
    max_aqi: Optional[int]
    min_aqi: Optional[int]
    aqi_trend: List[TimeSeriesPoint]
    pollutant_series: List[PollutantTimeSeries]
    dominant_pollutant: Optional[str]
    unhealthy_hours: int
    total_records: int


# ─── Alert Schemas ─────────────────────────────────────────────────────────────

class AlertResponse(BaseModel):
    id: int
    city_id: int
    city_name: Optional[str] = None
    alert_type: str
    channel: str
    aqi_value: int
    aqi_category: str
    message: str
    is_sent: bool
    sent_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Search Schemas ────────────────────────────────────────────────────────────

class CitySearchResult(BaseModel):
    name: str
    country: str
    country_code: str
    latitude: float
    longitude: float
    state: Optional[str] = None


# ─── General Response ──────────────────────────────────────────────────────────

class StatusResponse(BaseModel):
    status: str
    message: str
    data: Optional[dict] = None


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    per_page: int
    pages: int
