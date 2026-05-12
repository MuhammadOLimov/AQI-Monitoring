"""
AQI (Air Quality Index) Calculation Engine.

Implements US EPA AQI calculation method:
https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf

AQI Breakpoints and Categories:
  0–50    → Good
  51–100  → Moderate
  101–150 → Unhealthy for Sensitive Groups
  151–200 → Unhealthy
  201–300 → Very Unhealthy
  301+    → Hazardous
"""
from dataclasses import dataclass
from typing import Optional, Dict, Tuple


@dataclass
class AQICategory:
    label: str
    color: str
    hex_color: str
    description: str
    health_message: str


# AQI Categories definition
AQI_CATEGORIES: Dict[str, AQICategory] = {
    "Good": AQICategory(
        label="Good",
        color="green",
        hex_color="#00E400",
        description="Air quality is satisfactory",
        health_message="Air quality is considered satisfactory, and air pollution poses little or no risk.",
    ),
    "Moderate": AQICategory(
        label="Moderate",
        color="yellow",
        hex_color="#FFFF00",
        description="Air quality is acceptable",
        health_message="Air quality is acceptable. However, there may be a risk for some people, particularly those who are unusually sensitive to air pollution.",
    ),
    "Unhealthy for Sensitive Groups": AQICategory(
        label="Unhealthy for Sensitive Groups",
        color="orange",
        hex_color="#FF7E00",
        description="Members of sensitive groups may experience health effects",
        health_message="Members of sensitive groups may experience health effects. The general public is less likely to be affected.",
    ),
    "Unhealthy": AQICategory(
        label="Unhealthy",
        color="red",
        hex_color="#FF0000",
        description="Everyone may begin to experience health effects",
        health_message="Some members of the general public may experience health effects; members of sensitive groups may experience more serious health effects.",
    ),
    "Very Unhealthy": AQICategory(
        label="Very Unhealthy",
        color="purple",
        hex_color="#8F3F97",
        description="Health alert: everyone may experience more serious health effects",
        health_message="Health alert: The risk of health effects is increased for everyone.",
    ),
    "Hazardous": AQICategory(
        label="Hazardous",
        color="maroon",
        hex_color="#7E0023",
        description="Health warning of emergency conditions",
        health_message="Health warning of emergency conditions: everyone is more likely to be affected.",
    ),
}


# Breakpoints: (Concentration_Low, Concentration_High, AQI_Low, AQI_High)
# PM2.5 breakpoints (μg/m³, 24-hour average)
PM25_BREAKPOINTS = [
    (0.0, 12.0, 0, 50),
    (12.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 150.4, 151, 200),
    (150.5, 250.4, 201, 300),
    (250.5, 350.4, 301, 400),
    (350.5, 500.4, 401, 500),
]

# PM10 breakpoints (μg/m³, 24-hour average)
PM10_BREAKPOINTS = [
    (0, 54, 0, 50),
    (55, 154, 51, 100),
    (155, 254, 101, 150),
    (255, 354, 151, 200),
    (355, 424, 201, 300),
    (425, 504, 301, 400),
    (505, 604, 401, 500),
]

# CO breakpoints (ppm, 8-hour average) - converted from μg/m³ (divide by 1145.4)
CO_BREAKPOINTS_PPM = [
    (0.0, 4.4, 0, 50),
    (4.5, 9.4, 51, 100),
    (9.5, 12.4, 101, 150),
    (12.5, 15.4, 151, 200),
    (15.5, 30.4, 201, 300),
    (30.5, 40.4, 301, 400),
    (40.5, 50.4, 401, 500),
]

# NO2 breakpoints (ppb, 1-hour average) - converted from μg/m³ (divide by 1.88)
NO2_BREAKPOINTS_PPB = [
    (0, 53, 0, 50),
    (54, 100, 51, 100),
    (101, 360, 101, 150),
    (361, 649, 151, 200),
    (650, 1249, 201, 300),
    (1250, 1649, 301, 400),
    (1650, 2049, 401, 500),
]

# SO2 breakpoints (ppb, 1-hour average) - converted from μg/m³ (divide by 2.62)
SO2_BREAKPOINTS_PPB = [
    (0, 35, 0, 50),
    (36, 75, 51, 100),
    (76, 185, 101, 150),
    (186, 304, 151, 200),
    (305, 604, 201, 300),
    (605, 804, 301, 400),
    (805, 1004, 401, 500),
]

# O3 breakpoints (ppb, 8-hour average) - converted from μg/m³ (divide by 1.96)
O3_BREAKPOINTS_PPB = [
    (0, 54, 0, 50),
    (55, 70, 51, 100),
    (71, 85, 101, 150),
    (86, 105, 151, 200),
    (106, 200, 201, 300),
]


def _linear_interpolation(
    c: float,
    c_low: float,
    c_high: float,
    i_low: int,
    i_high: int,
) -> int:
    """EPA linear interpolation formula for AQI calculation."""
    return round(((i_high - i_low) / (c_high - c_low)) * (c - c_low) + i_low)


def _calc_sub_aqi(concentration: float, breakpoints: list) -> Optional[int]:
    """Calculate sub-index AQI for a single pollutant."""
    if concentration < 0:
        return None
    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= concentration <= c_high:
            return _linear_interpolation(concentration, c_low, c_high, i_low, i_high)
    # If above all breakpoints, cap at 500
    if concentration > breakpoints[-1][1]:
        return 500
    return None


def get_aqi_category(aqi: int) -> str:
    """Return AQI category label based on AQI value."""
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"


def get_aqi_color(aqi: int) -> str:
    """Return hex color for AQI value."""
    category = get_aqi_category(aqi)
    return AQI_CATEGORIES[category].hex_color


@dataclass
class AQIResult:
    aqi: int
    category: str
    color: str
    dominant_pollutant: str
    sub_indices: Dict[str, Optional[int]]
    health_message: str


def calculate_aqi(
    pm2_5: Optional[float] = None,
    pm10: Optional[float] = None,
    co: Optional[float] = None,     # μg/m³
    no2: Optional[float] = None,    # μg/m³
    so2: Optional[float] = None,    # μg/m³
    o3: Optional[float] = None,     # μg/m³
    nh3: Optional[float] = None,    # μg/m³ (no EPA breakpoints; use proxy)
) -> AQIResult:
    """
    Calculate US EPA AQI from pollutant concentrations.
    Returns the highest sub-index as the overall AQI (worst pollutant wins).

    All concentrations should be in μg/m³ (OpenWeatherMap default).
    """
    sub_indices: Dict[str, Optional[int]] = {}

    # PM2.5 - direct μg/m³
    if pm2_5 is not None:
        sub_indices["PM2.5"] = _calc_sub_aqi(pm2_5, PM25_BREAKPOINTS)

    # PM10 - direct μg/m³
    if pm10 is not None:
        sub_indices["PM10"] = _calc_sub_aqi(pm10, PM10_BREAKPOINTS)

    # CO - convert μg/m³ → ppm (1 ppm CO = 1145.4 μg/m³ at STP)
    if co is not None:
        co_ppm = co / 1145.4
        sub_indices["CO"] = _calc_sub_aqi(co_ppm, CO_BREAKPOINTS_PPM)

    # NO2 - convert μg/m³ → ppb (1 ppb NO2 = 1.88 μg/m³)
    if no2 is not None:
        no2_ppb = no2 / 1.88
        sub_indices["NO2"] = _calc_sub_aqi(no2_ppb, NO2_BREAKPOINTS_PPB)

    # SO2 - convert μg/m³ → ppb (1 ppb SO2 = 2.62 μg/m³)
    if so2 is not None:
        so2_ppb = so2 / 2.62
        sub_indices["SO2"] = _calc_sub_aqi(so2_ppb, SO2_BREAKPOINTS_PPB)

    # O3 - convert μg/m³ → ppb (1 ppb O3 = 1.96 μg/m³)
    if o3 is not None:
        o3_ppb = o3 / 1.96
        sub_indices["O3"] = _calc_sub_aqi(o3_ppb, O3_BREAKPOINTS_PPB)

    # NH3 - no official EPA breakpoints; use rough scale based on WHO guidelines
    # WHO 24h guideline: 100 μg/m³; mapped to AQI 100
    if nh3 is not None:
        nh3_aqi = min(int(nh3 * 1.0), 500)  # rough linear proxy
        sub_indices["NH3"] = nh3_aqi

    # Filter out None values
    valid_indices = {k: v for k, v in sub_indices.items() if v is not None}

    if not valid_indices:
        return AQIResult(
            aqi=0,
            category="Good",
            color="#00E400",
            dominant_pollutant="N/A",
            sub_indices=sub_indices,
            health_message=AQI_CATEGORIES["Good"].health_message,
        )

    # AQI = maximum sub-index
    dominant = max(valid_indices, key=lambda k: valid_indices[k])  # type: ignore
    aqi = valid_indices[dominant]  # type: ignore
    category = get_aqi_category(aqi)

    return AQIResult(
        aqi=aqi,
        category=category,
        color=AQI_CATEGORIES[category].hex_color,
        dominant_pollutant=dominant,
        sub_indices=sub_indices,
        health_message=AQI_CATEGORIES[category].health_message,
    )
