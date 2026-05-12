"""
Alert Service - sends Email notifications when AQI thresholds are exceeded.
"""
from datetime import datetime, timezone
from typing import Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger

from backend.core.config import settings
from backend.models.cities import City
from backend.models.air_quality import AirQualityRecord
from backend.models.alerts import Alert


class AlertService:
    """Manages AQI alerts via Email."""

    async def check_and_send_alert(
        self,
        db,
        city: City,
        record: AirQualityRecord,
    ) -> None:
        """Check thresholds and dispatch alerts if needed."""
        aqi = record.aqi
        if aqi <= settings.AQI_ALERT_THRESHOLD:
            return

        alert_type = "critical" if aqi >= settings.AQI_CRITICAL_THRESHOLD else "warning"
        message = self._build_message(city, record, alert_type)

        if settings.EMAIL_ALERTS_ENABLED:
            await self._send_email(db, city, record, alert_type, message)

    def _build_message(
        self, city: City, record: AirQualityRecord, alert_type: str
    ) -> str:
        emoji = "🔴" if alert_type == "critical" else "🟠"
        return (
            f"{emoji} *Air Quality Alert* - {alert_type.upper()}\n\n"
            f"📍 City: {city.name}, {city.country}\n"
            f"💨 AQI: *{record.aqi}* ({record.aqi_category})\n"
            f"🕐 Time: {record.timestamp.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"Pollutants:\n"
            f"  • PM2.5: {record.pm2_5 or 'N/A'} μg/m³\n"
            f"  • PM10:  {record.pm10 or 'N/A'} μg/m³\n"
            f"  • NO2:   {record.no2 or 'N/A'} μg/m³\n"
            f"  • SO2:   {record.so2 or 'N/A'} μg/m³\n"
            f"  • O3:    {record.o3 or 'N/A'} μg/m³\n"
            f"  • CO:    {record.co or 'N/A'} μg/m³\n\n"
            f"⚠️ Please take precautions!"
        )

    async def _send_email(
        self, db, city: City, record: AirQualityRecord,
        alert_type: str, message: str
    ) -> None:
        """Send email notification via SMTP."""
        alert = Alert(
            city_id=city.id,
            alert_type=alert_type,
            channel="email",
            aqi_value=record.aqi,
            aqi_category=record.aqi_category,
            message=message,
            is_sent=False,
        )
        db.add(alert)
        await db.flush()

        try:
            subject = f"[{alert_type.upper()}] Air Quality Alert - {city.name} AQI={record.aqi}"
            html_body = self._build_email_html(city, record, alert_type)

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.ALERT_EMAIL_FROM
            msg["To"] = settings.ALERT_EMAIL_TO
            msg.attach(MIMEText(message.replace("*", "").replace("_", ""), "plain"))
            msg.attach(MIMEText(html_body, "html"))

            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                start_tls=settings.SMTP_TLS,
            )

            alert.is_sent = True
            alert.sent_at = datetime.now(timezone.utc)
            logger.info(f"Email alert sent for {city.name} AQI={record.aqi}")
        except Exception as e:
            alert.error_message = str(e)
            logger.error(f"Email alert failed for {city.name}: {e}")

    def _build_email_html(
        self, city: City, record: AirQualityRecord, alert_type: str
    ) -> str:
        color = "#FF4444" if alert_type == "critical" else "#FF8C00"
        return f"""
        <html><body style="font-family:Arial,sans-serif;padding:20px;background:#f4f4f4">
        <div style="max-width:600px;margin:auto;background:white;border-radius:8px;overflow:hidden">
          <div style="background:{color};padding:20px;text-align:center">
            <h1 style="color:white;margin:0">Air Quality Alert</h1>
            <p style="color:white;margin:5px 0">{alert_type.upper()}</p>
          </div>
          <div style="padding:30px">
            <h2>📍 {city.name}, {city.country}</h2>
            <div style="text-align:center;padding:20px">
              <div style="background:{color};border-radius:50%;width:120px;height:120px;
                          margin:auto;display:flex;align-items:center;justify-content:center">
                <span style="color:white;font-size:36px;font-weight:bold">{record.aqi}</span>
              </div>
              <p style="font-size:18px;color:{color};font-weight:bold">{record.aqi_category}</p>
            </div>
            <table style="width:100%;border-collapse:collapse">
              <tr><td style="padding:8px;border-bottom:1px solid #eee"><b>PM2.5</b></td>
                  <td style="padding:8px;border-bottom:1px solid #eee">{record.pm2_5 or 'N/A'} μg/m³</td></tr>
              <tr><td style="padding:8px;border-bottom:1px solid #eee"><b>PM10</b></td>
                  <td style="padding:8px;border-bottom:1px solid #eee">{record.pm10 or 'N/A'} μg/m³</td></tr>
              <tr><td style="padding:8px;border-bottom:1px solid #eee"><b>NO2</b></td>
                  <td style="padding:8px;border-bottom:1px solid #eee">{record.no2 or 'N/A'} μg/m³</td></tr>
              <tr><td style="padding:8px;border-bottom:1px solid #eee"><b>SO2</b></td>
                  <td style="padding:8px;border-bottom:1px solid #eee">{record.so2 or 'N/A'} μg/m³</td></tr>
            </table>
            <p style="margin-top:20px;color:#666;font-size:14px">
              Recorded at: {record.timestamp.strftime('%Y-%m-%d %H:%M UTC')}
            </p>
          </div>
        </div>
        </body></html>
        """


alert_service = AlertService()
