# АСУ «Магазин» (Django + Vue + PostgreSQL)

Учебный/практический проект для директора продовольственного магазина.

## 1) Что уже реализовано

- Backend: Django + DRF, роли `admin` / `user`, CRUD, бизнес-операции.
- Frontend: Vue 3 + Vite + npm.
- БД: PostgreSQL (основной режим), SQLite (временный fallback).
- Документы: PDF-заявка на закупку.
- Отчеты: ежемесячный отчет по отделам с расчетом прибыли.

## 2) Главная причина твоей ошибки на фронте

Ошибка вида:

`Unexpected token '﻿', "﻿{ ... }" is not valid JSON`

означает BOM в начале JSON/JS/CSS-файлов. В проекте это исправлено (файлы пересохранены в UTF-8 без BOM).

## 3) Важно про PostgreSQL

`pgAdmin` сам по себе не является сервером БД. Нужен установленный **PostgreSQL Server**.

Проверка в PowerShell:

```powershell
psql --version
```

Если команда не найдена, значит сервер/клиент PostgreSQL не установлен или не добавлен в PATH.

## 4) Локальный запуск без Docker (рекомендуется начать так)

### Шаг 1. Python окружение

```powershell
cd D:\Kurs
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
```

### Шаг 2. Настройка `.env`

```powershell
Copy-Item .env.example .env
```

В `.env` должны быть параметры PostgreSQL:

```env
POSTGRES_DB=shop_db
POSTGRES_USER=shop_user
POSTGRES_PASSWORD=shop_pass
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
USE_SQLITE=0
```

### Шаг 3. Создать БД и пользователя (один раз)

Вариант через `psql`:

```sql
CREATE USER shop_user WITH PASSWORD 'shop_pass';
CREATE DATABASE shop_db OWNER shop_user;
GRANT ALL PRIVILEGES ON DATABASE shop_db TO shop_user;
```

Если `shop_user` уже создан, выполняй только `CREATE DATABASE ... OWNER ...`.

Или автоматически скриптом:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_postgres.ps1
```

### Шаг 4. Миграции и демо-данные

```powershell
.\.venv\Scripts\python backend\manage.py migrate
.\.venv\Scripts\python backend\manage.py seed_demo
```

Демо-пользователи:
- `admin / admin12345`
- `operator / user12345`

### Шаг 5. Запуск backend

```powershell
.\.venv\Scripts\python backend\manage.py runserver 127.0.0.1:8000
```

Проверка:
- [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- [http://127.0.0.1:8000/api/](http://127.0.0.1:8000/api/)

### Шаг 6. Запуск frontend

```powershell
cd D:\Kurs\frontend
npm install
npm run dev
```

Открыть:
- [http://127.0.0.1:5173](http://127.0.0.1:5173)

## 5) Если PostgreSQL еще не установлен

Временный режим (чтобы продолжать разработку):

```env
USE_SQLITE=1
```

И далее:

```powershell
.\.venv\Scripts\python backend\manage.py migrate
.\.venv\Scripts\python backend\manage.py seed_demo
.\.venv\Scripts\python backend\manage.py runserver 127.0.0.1:8000
```

Потом возвращаешь `USE_SQLITE=0` и переходишь на PostgreSQL.

## 6) Git поток (dev/prod)

В репозитории уже есть:
- ветка `main`
- ветка `develop`
- workflow: `.github/workflows/docker-images.yml`

Логика:
- push в `develop` -> build/push docker-образов с тегами `dev` и `dev-<sha>`
- push тега `v*` (например `v1.0.0`) -> build/push версии и `latest` (prod)

## 7) Подключение к GitHub

```powershell
cd D:\Kurs
git remote add origin <ТВОЙ_URL_РЕПО>
git push -u origin main
git push -u origin develop
```

Релиз в prod:

```powershell
git tag v1.0.0
git push origin v1.0.0
```

## 8) Когда нужен Docker

Сейчас Docker не обязателен. Для обучения/разработки запускай без Docker.

Docker нужен, когда:
- хочешь одинаковый запуск на любом ПК одной командой;
- хочешь проще показывать проект преподавателю/заказчику;
- хочешь стабильно использовать CI/CD образы dev/prod.
