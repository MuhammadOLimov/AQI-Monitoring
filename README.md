# 🌍 AirWatch — Real-time Air Pollution Monitoring System

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

Real-time air quality monitoring platform that collects, calculates, stores, and visualizes AQI data from OpenWeatherMap API for cities worldwide.

---

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Docker Deployment](#docker-deployment)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [AQI Calculation](#aqi-calculation)
- [Alert System](#alert-system)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔄 **Real-time Data** | Fetches air quality data every 30 minutes via OpenWeatherMap API |
| 📊 **AQI Engine** | US EPA standard AQI calculation for PM2.5, PM10, CO, NO2, SO2, O3 |
| 🗺️ **Interactive Map** | Leaflet.js map with live markers, popups, and pollution heatmap |
| 📈 **Charts** | Chart.js time-series for all 7 pollutants + AQI trend |
| 🔔 **Alerts** | Email (SMTP) notifications when AQI threshold exceeded |
| 📋 **History** | Full historical data with date-range filtering |
| ⬇️ **CSV Export** | One-click data export for any city/period |
| 🌙 **Dark/Light Mode** | Toggle between themes |
| 🐳 **Docker Ready** | Full docker-compose with Nginx, PostgreSQL, Redis |
| ⚙️ **Admin Panel** | City management, bulk fetch, system health |
| 📖 **Auto Docs** | Swagger UI + ReDoc at `/docs` and `/redoc` |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    NGINX (Port 80)                       │
│              Reverse Proxy + Static Files                │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│              FastAPI Application (Port 8000)             │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │ /cities  │  │/air-qual │  │ /alerts  │  │ /admin │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
│                                                          │
│  ┌─────────────────┐  ┌────────────────────────────┐    │
│  │  AQI Calculator │  │  Background Scheduler      │    │
│  │  (EPA Standard) │  │  (APScheduler, 30min)      │    │
│  └─────────────────┘  └────────────────────────────┘    │
│                                                          │
│  ┌─────────────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ OpenWeather API │  │ Email (SMTP) │   │
│  │   Integration   │  │  Alerts  │  │    Alerts    │   │
│  └─────────────────┘  └──────────┘  └──────────────┘   │
└───────────────────────┬─────────────────────────────────┘
                        │
              ┌─────────┴─────────┐
              │                   │
   ┌──────────▼────┐   ┌─────────▼──────┐
   │  PostgreSQL   │   │     Redis      │
   │  (Main DB)    │   │    (Cache)     │
   └───────────────┘   └────────────────┘
```

---

## 📁 Project Structure

```
air-pollution-monitor/
├── main.py                          # FastAPI app entry point
├── requirements.txt
├── alembic.ini
├── .env.example
├── Dockerfile
├── docker-compose.yml
│
├── backend/
│   ├── core/
│   │   ├── config.py               # Pydantic Settings configuration
│   │   ├── database.py             # SQLAlchemy async engine & sessions
│   │   └── logging.py              # Loguru structured logging
│   │
│   ├── models/
│   │   ├── cities.py               # City ORM model
│   │   ├── air_quality.py          # AirQualityRecord ORM model
│   │   └── alerts.py               # Alert ORM model
│   │
│   ├── schemas/
│   │   └── schemas.py              # Pydantic request/response schemas
│   │
│   ├── services/
│   │   ├── openweather_service.py  # OpenWeatherMap API client
│   │   ├── air_quality_service.py  # Business logic layer
│   │   ├── city_service.py         # City CRUD operations
│   │   ├── alert_service.py        # Email notifications
│   │   └── scheduler.py            # APScheduler background tasks
│   │
│   ├── routers/
│   │   ├── health.py               # GET /health
│   │   ├── cities.py               # CRUD /api/v1/cities
│   │   ├── air_quality.py          # Data & analytics endpoints
│   │   ├── alerts.py               # Alert history
│   │   └── admin.py                # Admin panel route
│   │
│   └── utils/
│       └── aqi_calculator.py       # US EPA AQI calculation engine
│
├── frontend/
│   ├── templates/
│   │   ├── dashboard.html          # Main SPA dashboard
│   │   └── admin.html              # Admin panel
│   └── static/
│       ├── css/                    # Additional stylesheets
│       ├── js/                     # Additional scripts
│       └── assets/                 # Images, icons
│
├── database/
│   ├── env.py                      # Alembic environment
│   └── versions/
│       └── 001_initial.py          # Initial schema migration
│
├── docker/
│   ├── nginx.conf                  # Nginx reverse proxy config
│   └── init.sql                    # PostgreSQL initialization
│
└── logs/                           # Application logs (auto-created)
    ├── app.log
    └── error.log
```

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- OpenWeatherMap API key (free at [openweathermap.org](https://openweathermap.org/api))

### Step 1: Clone & Setup

```bash
git clone https://github.com/yourname/air-pollution-monitor.git
cd air-pollution-monitor

# Create virtual environment
python -m venv venv
source venv/bin/activate          # Linux/macOS
# venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your settings:
```env
# REQUIRED
OPENWEATHER_API_KEY=your_key_here
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/air_pollution_db
DATABASE_SYNC_URL=postgresql://postgres:password@localhost:5432/air_pollution_db

# OPTIONAL (for email alerts)
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_ALERTS_ENABLED=true
```

### Step 3: Create Database

```bash
# Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE air_pollution_db;"

# Run Alembic migrations
alembic upgrade head
```

### Step 4: Run Application

```bash
python main.py
```

Open browser: **http://localhost:8000/dashboard**

API Docs: **http://localhost:8000/docs**

Admin Panel: **http://localhost:8000/admin**

---

## 🐳 Docker Deployment

### Quick Deploy

```bash
# 1. Copy and configure environment
cp .env.example .env
# Edit .env: add OPENWEATHER_API_KEY at minimum

# 2. Start all services
docker-compose up -d

# 3. Check status
docker-compose ps
docker-compose logs -f api
```

Services will be available at:
- Dashboard: http://localhost/dashboard
- API Docs: http://localhost/docs
- Admin: http://localhost/admin

### Docker Commands

```bash
# Stop services
docker-compose down

# Stop and remove volumes (DELETES ALL DATA)
docker-compose down -v

# Rebuild after code changes
docker-compose up -d --build api

# View logs
docker-compose logs -f api
docker-compose logs -f db

# Access PostgreSQL
docker-compose exec db psql -U postgres -d air_pollution_db

# Run migrations
docker-compose exec api alembic upgrade head
```

---

## ⚙️ Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENWEATHER_API_KEY` | **required** | OpenWeatherMap free API key |
| `DATABASE_URL` | — | Async PostgreSQL URL |
| `DATABASE_SYNC_URL` | — | Sync PostgreSQL URL (for Alembic) |
| `DATA_FETCH_INTERVAL` | `1800` | Fetch interval in seconds (1800 = 30 min) |
| `AUTO_FETCH_CITIES` | `Tashkent,...` | Comma-separated cities to auto-monitor |
| `AQI_ALERT_THRESHOLD` | `100` | AQI level that triggers warning alert |
| `AQI_CRITICAL_THRESHOLD` | `200` | AQI level that triggers critical alert |

| `SMTP_HOST` | `smtp.gmail.com` | SMTP server hostname |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USERNAME` | — | SMTP username (email address) |
| `SMTP_PASSWORD` | — | App password (not account password) |
| `EMAIL_ALERTS_ENABLED` | `false` | Enable email notifications |

---

## 📡 API Documentation

### Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health check |
| GET | `/api/v1/cities/` | List all cities |
| POST | `/api/v1/cities/` | Create city manually |
| GET | `/api/v1/cities/search/geocode?q=London` | Geocode search |
| POST | `/api/v1/cities/search/add?q=London` | Auto-add city |
| GET | `/api/v1/air-quality/latest` | Latest data all cities |
| GET | `/api/v1/air-quality/city/{id}/latest` | Latest for one city |
| GET | `/api/v1/air-quality/city/{id}/history` | Historical records |
| GET | `/api/v1/air-quality/city/{id}/analytics?days=7` | Analytics & stats |
| POST | `/api/v1/air-quality/city/{id}/fetch` | Manual fetch trigger |
| POST | `/api/v1/air-quality/fetch-all` | Fetch all cities now |
| GET | `/api/v1/air-quality/city/{id}/export/csv` | CSV export |
| GET | `/api/v1/alerts/` | Alert history |

Full interactive docs at `/docs` (Swagger UI) or `/redoc`.

---

## 🧮 AQI Calculation

Uses **US EPA standard breakpoints** for linear interpolation:

```
AQI = ((I_high - I_low) / (C_high - C_low)) × (C - C_low) + I_low
```

| Pollutant | Standard | Unit | Conversion |
|-----------|----------|------|------------|
| PM2.5 | EPA 24h | μg/m³ | Direct |
| PM10 | EPA 24h | μg/m³ | Direct |
| CO | EPA 8h | ppm | ÷ 1145.4 |
| NO2 | EPA 1h | ppb | ÷ 1.88 |
| SO2 | EPA 1h | ppb | ÷ 2.62 |
| O3 | EPA 8h | ppb | ÷ 1.96 |

AQI = maximum sub-index across all pollutants.

### AQI Categories

| Range | Category | Color | Action |
|-------|----------|-------|--------|
| 0–50 | Good | 🟢 `#00E400` | Normal outdoor activities |
| 51–100 | Moderate | 🟡 `#FFFF00` | Unusually sensitive people should limit prolonged exertion |
| 101–150 | Unhealthy for Sensitive Groups | 🟠 `#FF7E00` | Sensitive groups reduce prolonged outdoor exertion |
| 151–200 | Unhealthy | 🔴 `#FF0000` | Everyone reduce prolonged outdoor exertion |
| 201–300 | Very Unhealthy | 🟣 `#8F3F97` | Everyone avoid prolonged outdoor exertion |
| 301+ | Hazardous | ⬛ `#7E0023` | Avoid all outdoor exertion |

---

## 🔔 Alert System

### Email (Gmail) Setup

1. Enable 2-Factor Authentication on Gmail
2. Generate App Password: Google Account → Security → App Passwords
3. Set in `.env`:
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=you@gmail.com
   SMTP_PASSWORD=your_app_password
   ALERT_EMAIL_FROM=noreply@yourapp.com
   ALERT_EMAIL_TO=admin@yourapp.com
   EMAIL_ALERTS_ENABLED=true
   ```

---

## 🔧 Development

### Run Tests
```bash
pytest tests/ -v --asyncio-mode=auto
```

### Code Formatting
```bash
black backend/ main.py
isort backend/ main.py
```

### Create New Migration
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Credits

- [OpenWeatherMap](https://openweathermap.org) — Air pollution data
- [US EPA](https://www.epa.gov/outdoor-air-quality-data) — AQI methodology
- [FastAPI](https://fastapi.tiangolo.com) — Web framework
- [Chart.js](https://chartjs.org) — Data visualization
- [Leaflet.js](https://leafletjs.com) — Interactive maps
