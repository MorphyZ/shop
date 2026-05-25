# АСУ «Магазин» (Django + Vue + PostgreSQL)

Проект для автоматизации учета товаров, закупок, продаж и отчетности магазина.

## Что реализовано

- Backend: Django + DRF, роли `admin` и `user`, CRUD и бизнес-операции.
- Frontend: Vue 3 + Vite (`npm` проект).
- БД: PostgreSQL (основной режим), SQLite (только как временный fallback).
- Документы: PDF-заявка на закупку.
- Отчеты: ежемесячный отчет по отделам с расчетом прибыли.

## Быстрый запуск без Docker

### 1) Установка зависимостей Python

```powershell
cd D:\Kurs
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
```

### 2) Настройка переменных окружения

```powershell
Copy-Item .env.example .env
```

Проверь, что в `.env`:

```env
POSTGRES_DB=shop_db
POSTGRES_USER=shop_user
POSTGRES_PASSWORD=shop_pass
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
USE_SQLITE=0
```

### 3) Автонастройка PostgreSQL (создание роли и БД)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_postgres.ps1
```

### 4) Миграции и демо-данные

```powershell
.\.venv\Scripts\python backend\manage.py migrate
.\.venv\Scripts\python backend\manage.py seed_demo
```

### 5) Запуск backend

```powershell
.\.venv\Scripts\python backend\manage.py runserver 127.0.0.1:8000
```

Проверка:
- http://127.0.0.1:8000/admin/
- http://127.0.0.1:8000/api/

### 6) Запуск frontend

```powershell
cd D:\Kurs\frontend
npm install
npm run dev
```

Открыть:
- http://127.0.0.1:5173

## Демо-пользователи

- `admin / admin12345`
- `operator / user12345`

## pgAdmin и PostgreSQL

- `pgAdmin` — это клиент для управления, не сервер БД.
- После запуска скрипта `setup_postgres.ps1` у тебя будет БД `shop_db` и пользователь `shop_user`.
- В pgAdmin открой:
  - `Servers` -> твой сервер PostgreSQL
  - `Databases` -> должна быть `shop_db`
  - если не видно, нажми `Refresh` на узле `Databases`.

## Git-поток

- `main` — основная ветка.
- `develop` — ветка разработки.
- Workflow `.github/workflows/docker-images.yml`:
  - push в `develop` -> собираются dev-образы;
  - push тега `v*` -> собираются prod-образы.

## Запуск через Docker (позже)

Когда захочешь перейти на Docker:

```powershell
docker compose up --build
```

Для production:

```powershell
docker compose -f docker-compose.prod.yml up --build -d
```