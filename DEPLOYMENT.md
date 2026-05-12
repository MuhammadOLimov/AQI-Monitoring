# Production Deployment Guide

Ushbu loyiha Docker va Docker Compose yordamida production muhitiga deploy qilish uchun to'liq tayyorlangan.

## Talablar
- Docker (20.10+)
- Docker Compose (v2.0+)

## Tezkor ishga tushirish

1. **Loyiha fayllarini serverga nusxalash:**
   ```bash
   git clone <repo-url>
   cd air-pollution-monitor
   ```

2. **Muhit o'zgaruvchilarini sozlash:**
   `.env.example` faylidan `.env` faylini yarating va kerakli qiymatlarni (ayniqsa `OPENWEATHER_API_KEY` va `SECRET_KEY`) kiriting:
   ```bash
   cp .env.example .env
   nano .env
   ```

3. **Docker konteynerlarini qurish va ishga tushirish:**
   ```bash
   docker compose up --build -d
   ```

4. **Holatni tekshirish:**
   ```bash
   docker compose ps
   docker compose logs -f api
   ```

## Servislar va Portlar
- **Frontend & API (Nginx):** `http://your-server-ip/dashboard` (80-port)
- **Backend API (Direct):** `http://your-server-ip:8000/docs`
- **Database:** PostgreSQL (5432-port, faqat ichki tarmoqda yoki sozlamaga qarab)

## Monitoring va Loglar
Loglar loyiha ildizidagi `logs/` papkasida saqlanadi. Shuningdek, docker orqali ko'rish mumkin:
```bash
docker compose logs -f api
```

## Ma'lumotlar bazasi migratsiyalari
Migratsiyalar ilova ishga tushganda avtomatik ravishda (Alembic orqali) tekshiriladi va jadval yaratiladi (`main.py` dagi `create_tables` funksiyasi orqali).

## SSL (HTTPS) sozlash
Nginx konteyneri SSL uchun tayyorlangan, biroq sertifikatlarni o'zingiz (masalan, Let's Encrypt / Certbot yordamida) qo'shishingiz kerak. Buning uchun `docker/nginx.conf` faylini tahrirlang va 443-portni oching.

## Muhim eslatmalar
- Productionda har doim `DEBUG=false` ekanligiga ishonch hosil qiling.
- `SECRET_KEY` va `ADMIN_PASSWORD` ni kuchli qiymatlarga almashtiring.
- Database paroli `.env` da ko'rsatilgan bo'lishi kerak.
