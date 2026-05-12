"""
Alert model - stores sent notifications and alert history.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    city_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alert_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "warning" | "critical"
    channel: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "email" | "system"
    aqi_value: Mapped[int] = mapped_column(Integer, nullable=False)
    aqi_category: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship
    city: Mapped["City"] = relationship("City", back_populates="alerts")

    def __repr__(self) -> str:
        return (
            f"<Alert(id={self.id}, city_id={self.city_id}, "
            f"type={self.alert_type}, aqi={self.aqi_value})>"
        )
