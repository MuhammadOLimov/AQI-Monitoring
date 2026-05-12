"""
Unit tests for AQI calculation engine.
Run: pytest tests/ -v
"""
import pytest
from backend.utils.aqi_calculator import (
    calculate_aqi,
    get_aqi_category,
    get_aqi_color,
    _calc_sub_aqi,
    PM25_BREAKPOINTS,
)


class TestAQICategory:
    def test_good(self):
        assert get_aqi_category(0) == "Good"
        assert get_aqi_category(25) == "Good"
        assert get_aqi_category(50) == "Good"

    def test_moderate(self):
        assert get_aqi_category(51) == "Moderate"
        assert get_aqi_category(75) == "Moderate"
        assert get_aqi_category(100) == "Moderate"

    def test_sensitive(self):
        assert get_aqi_category(101) == "Unhealthy for Sensitive Groups"
        assert get_aqi_category(150) == "Unhealthy for Sensitive Groups"

    def test_unhealthy(self):
        assert get_aqi_category(151) == "Unhealthy"
        assert get_aqi_category(200) == "Unhealthy"

    def test_very_unhealthy(self):
        assert get_aqi_category(201) == "Very Unhealthy"
        assert get_aqi_category(300) == "Very Unhealthy"

    def test_hazardous(self):
        assert get_aqi_category(301) == "Hazardous"
        assert get_aqi_category(500) == "Hazardous"


class TestAQIColors:
    def test_colors_not_empty(self):
        for aqi in [0, 50, 100, 150, 200, 300, 400]:
            color = get_aqi_color(aqi)
            assert color.startswith("#")
            assert len(color) == 7


class TestAQICalculation:
    def test_clean_air(self):
        result = calculate_aqi(pm2_5=5.0, pm10=10.0)
        assert result.aqi <= 50
        assert result.category == "Good"

    def test_moderate_pm25(self):
        result = calculate_aqi(pm2_5=20.0)
        assert 51 <= result.aqi <= 100
        assert result.category == "Moderate"

    def test_unhealthy_pm25(self):
        result = calculate_aqi(pm2_5=100.0)
        assert result.aqi > 100

    def test_dominant_pollutant_selected(self):
        # High PM2.5 but low PM10 — PM2.5 should dominate
        result = calculate_aqi(pm2_5=100.0, pm10=5.0)
        assert result.dominant_pollutant == "PM2.5"

    def test_no_data_returns_zero(self):
        result = calculate_aqi()
        assert result.aqi == 0
        assert result.category == "Good"

    def test_sub_indices_populated(self):
        result = calculate_aqi(pm2_5=15.0, no2=30.0, o3=60.0)
        assert "PM2.5" in result.sub_indices
        assert "NO2" in result.sub_indices
        assert "O3" in result.sub_indices

    def test_pm25_breakpoint_good(self):
        aqi = _calc_sub_aqi(6.0, PM25_BREAKPOINTS)
        assert aqi is not None
        assert 0 <= aqi <= 50

    def test_pm25_breakpoint_moderate(self):
        aqi = _calc_sub_aqi(25.0, PM25_BREAKPOINTS)
        assert aqi is not None
        assert 51 <= aqi <= 100

    def test_very_high_caps_at_500(self):
        result = calculate_aqi(pm2_5=1000.0)
        assert result.aqi == 500
