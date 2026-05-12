# AirWatch — Installation & Deployment Guide

## 🔑 Prerequisites

| Tool | Minimum Version | Notes |
|------|----------------|-------|
| Python | 3.11+ | Use pyenv for version management |
| PostgreSQL | 14+ | Or use Docker |
| Redis | 7+ | Or use Docker |
| Docker | 24+ | For containerized deployment |
| Docker Compose | 2.20+ | Included in Docker Desktop |

---

## 📦 Method 1: Local Development Setup

### 1. Python Environment

```bash
# Clone project
git clone https://github.com/yourname/air-pollution-monitor.git
cd air-pollution-monitor

# Create isolated virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate          # macOS / Linux
venv\Scripts\activate.bat         # Windows CMD
venv\Scripts\Activate.ps1         # Windows PowerShell

# Install all dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. PostgreSQL Setup

```bash
# macOS (Homebrew)
brew install postgresql@16
brew services start postgresql@16

# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# Create database
sudo -u postgres psql
```

```sql
-- Inside psql:
CREATE USER airwatch WITH PASSWORD 'strongpassword';
CREATE DATABASE air_pollution_db OWNER airwatch;
GRANT ALL PRIVILEGES ON DATABASE air_pollution_db TO airwatch;
\q
```

### 3. Redis Setup

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis-server

# Verify
redis-cli ping   # Should return: PONG
```

### 4. Environment Variables

```bash
cp .env.example .env
nano .env    # or use your preferred editor
```

**Minimum required variables:**
```env
OPENWEATHER_API_KEY=your_api_key_here
DATABASE_URL=postgresql+asyncpg://airwatch:strongpassword@localhost:5432/air_pollution_db
DATABASE_SYNC_URL=postgresql://airwatch:strongpassword@localhost:5432/air_pollution_db
```

### 5. Database Migration

```bash
# Apply all migrations
alembic upgrade head

# Verify tables were created
psql -U airwatch -d air_pollution_db -c "\dt"
```

### 6. Run the Server

```bash
# Development mode (auto-reload)
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Access points:**
| URL | Description |
|-----|-------------|
| http://localhost:8000/dashboard | Main Dashboard |
| http://localhost:8000/admin | Admin Panel |
| http://localhost:8000/docs | Swagger API Docs |
| http://localhost:8000/redoc | ReDoc API Docs |
| http://localhost:8000/health | Health Check |

---

## 🐳 Method 2: Docker Compose (Recommended for Production)

### 1. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` — at minimum set:
```env
OPENWEATHER_API_KEY=your_actual_api_key
DB_PASSWORD=choose_a_strong_password
SECRET_KEY=generate_a_32char_random_string
```

Generate secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Start All Services

```bash
# Start in background
docker-compose up -d

# Watch startup logs
docker-compose logs -f

# Check all services are running
docker-compose ps
```

Expected output:
```
NAME                IMAGE       STATUS          PORTS
airwatch_db         postgres    healthy         5432/tcp
airwatch_redis      redis       healthy         6379/tcp
airwatch_api        airwatch    healthy         8000/tcp
airwatch_nginx      nginx       running         0.0.0.0:80->80/tcp
```

### 3. Run Database Migrations

```bash
docker-compose exec api alembic upgrade head
```

### 4. Access the Application

- Dashboard: http://localhost/dashboard
- Admin: http://localhost/admin
- API Docs: http://localhost/docs

---

## ☁️ Method 3: Production Deployment (Ubuntu VPS)

### Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt install docker-compose-plugin

# Clone project
git clone https://github.com/yourname/air-pollution-monitor.git /opt/airwatch
cd /opt/airwatch
```

### Configure for Production

```bash
cp .env.example .env
nano .env
```

Set production values:
```env
APP_ENV=production
DEBUG=false
RELOAD=false
WORKERS=4
OPENWEATHER_API_KEY=your_key
DB_PASSWORD=very_strong_password_here
SECRET_KEY=your_32_char_secret_key
CORS_ALLOW_ALL=false
CORS_ORIGINS=https://yourdomain.com
```

### Deploy with Systemd

```bash
# Create systemd service
sudo nano /etc/systemd/system/airwatch.service
```

```ini
[Unit]
Description=AirWatch Air Pollution Monitor
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/airwatch
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable airwatch
sudo systemctl start airwatch
sudo systemctl status airwatch
```

### HTTPS with Let's Encrypt (Optional)

```bash
# Install Certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Update nginx.conf to use SSL
# (edit docker/nginx.conf to add SSL config)

# Auto-renew
sudo crontab -e
# Add: 0 12 * * * certbot renew --quiet && docker-compose exec nginx nginx -s reload
```

---

## 🔧 Maintenance Commands

### Logs

```bash
# Application logs
docker-compose logs -f api
tail -f logs/app.log
tail -f logs/error.log

# Nginx logs
docker-compose logs -f nginx
```

### Database Backups

```bash
# Create backup
docker-compose exec db pg_dump -U postgres air_pollution_db > backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose exec -T db psql -U postgres air_pollution_db < backup_20240101.sql

# Automated daily backup (add to crontab)
0 2 * * * cd /opt/airwatch && docker-compose exec -T db pg_dump -U postgres air_pollution_db > /backups/db_$(date +\%Y\%m\%d).sql
```

### Updates

```bash
cd /opt/airwatch
git pull origin main
docker-compose down
docker-compose build api
docker-compose up -d
docker-compose exec api alembic upgrade head
```

### Cleanup Old Data

```bash
# Connect to DB and delete records older than 90 days
docker-compose exec db psql -U postgres air_pollution_db -c \
  "DELETE FROM air_quality_records WHERE created_at < NOW() - INTERVAL '90 days';"
```

---

## 🐛 Troubleshooting

### Database connection refused
```bash
# Check PostgreSQL is running
docker-compose ps db
docker-compose logs db

# Verify credentials
docker-compose exec db psql -U postgres -c "\l"
```

### API key errors (401/403 from OpenWeatherMap)
- Verify key at https://openweathermap.org/api_keys
- New keys take up to 2 hours to activate
- Free tier allows 60 calls/minute

### No data showing in dashboard
```bash
# Manually trigger fetch
curl -X POST http://localhost:8000/api/v1/air-quality/fetch-all

# Check scheduler is running
curl http://localhost:8000/health
```

### Port 80 already in use
```bash
# Find what's using port 80
sudo lsof -i :80
sudo fuser -k 80/tcp

# Or change nginx port in docker-compose.yml
ports:
  - "8080:80"
```
