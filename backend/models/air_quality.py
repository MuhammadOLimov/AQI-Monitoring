"""
Air Quality Record model - stores all pollution measurements.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class AirQualityRecord(Base):
    __tablename__ = "air_quality_records"

    __table_args__ = (
        Index("ix_aqr_city_timestamp", "city_id", "timestamp"),
        Index("ix_aqr_timestamp", "timestamp"),
        Index("ix_aqr_aqi", "aqi"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    city_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # AQI
    aqi: Mapped[int] = mapped_column(Integer, nullable=False)
    aqi_category: Mapped[str] = mapped_column(String(50), nullable=False)

    # Pollutants (μg/m³ unless noted)
    pm2_5: Mapped[Optional[float]] = mapped_column(Float, nullable=True)   # PM2.5
    pm10: Mapped[Optional[float]] = mapped_column(Float, nullable=True)    # PM10
    co: Mapped[Optional[float]] = mapped_column(Float, nullable=True)      # CO (μg/m³)
    no2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)     # NO2
    so2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)     # SO2
    o3: Mapped[Optional[float]] = mapped_column(Float, nullable=True)      # Ozone
    nh3: Mapped[Optional[float]] = mapped_column(Float, nullable=True)     # Ammonia
    no: Mapped[Optional[float]] = mapped_column(Float, nullable=True)      # NO
    nox: Mapped[Optional[float]] = mapped_column(Float, nullable=True)     # NOx

    # OpenWeather native AQI (1-5 scale)
    ow_aqi: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship
    city: Mapped["City"] = relationship("City", back_populates="air_quality_records")

    def __repr__(self) -> str:
        return (
            f"<AirQualityRecord(id={self.id}, city_id={self.city_id}, "
            f"aqi={self.aqi}, timestamp={self.timestamp})>"
        )
