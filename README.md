# АСУ «Магазин» (Django + Vue + PostgreSQL)

Веб-приложение для директора продовольственного магазина.

## Что реализовано

- Backend: `Django + DRF` с бизнес-логикой закупок, продаж и отчетов.
- Frontend: `Vue 3 + Vite` (с `npm` зависимостями и адаптивным интерфейсом).
- БД: `PostgreSQL` (есть fallback в `SQLite` для быстрой локальной проверки).
- Роли: `admin` и `user`.
- Валидация:
  - серверная: сериализаторы, ограничения моделей, бизнес-проверки;
  - клиентская: required-поля, числовые ограничения, проверки перед отправкой.
- Документы и отчеты:
  - PDF-заявка на закупку;
  - ежемесячный отчет по отделам с прибылью.

## Предметная модель (10 таблиц)

1. `Store` — магазин (класс, номер)
2. `Department` — отдел (с заведующим, статусом открыт/закрыт)
3. `SupplierBase` — торговая база
4. `Product` — товар
5. `BaseStock` — остатки товара на базах
6. `DepartmentStock` — остатки товара в отделах
7. `PurchaseOrder` — закупка
8. `PurchaseOrderItem` — позиции закупки
9. `Sale` — продажа
10. `SaleItem` — позиции продажи

## Функции из задания

- Какие товары есть в магазине: `GET /api/dashboard/store-products/?store_id=...`
- Какие товары есть на базе: `GET /api/dashboard/base-products/`
- Какие отсутствующие товары можно заказать: `GET /api/dashboard/missing-products/?store_id=...`
- Какие товары и в каком количестве есть в отделе: `GET /api/departments/{id}/inventory/`
- Список заведующих: `GET /api/dashboard/managers/?store_id=...`
- Суммарная стоимость по отделам: `GET /api/dashboard/department-values/?store_id=...`
- На каких базах и в каких количествах есть товар: `GET /api/dashboard/product-bases/?product_name=...`
- Оприходование закупки: `POST /api/purchase-orders/{id}/receive/`
- PDF-заявка: `GET /api/purchase-orders/{id}/document/`
- Ежемесячный отчет: `GET /api/reports/monthly/?store_id=...&year=...&month=...`

## Роли

- `admin`: полный доступ (CRUD, ценообразование, открытие/закрытие отделов, перемещение товара, закупки).
- `user`: просмотр данных и проведение продаж.

Демо-пользователи (после `seed_demo`):

- `admin / admin12345`
- `operator / user12345`

## Локальный запуск (без Docker)

### 1) Backend

```powershell
cd D:\Kurs
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
```

Заполни `.env` для PostgreSQL (или включи временно `USE_SQLITE=1`).

```powershell
.\.venv\Scripts\python backend\manage.py migrate
.\.venv\Scripts\python backend\manage.py seed_demo
.\.venv\Scripts\python backend\manage.py runserver
```

### 2) Frontend (npm обязателен)

```powershell
cd D:\Kurs\frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`  
Backend: `http://localhost:8000`

## Запуск через Docker (лучший вариант для показа на другом ПК)

```powershell
cd D:\Kurs
Copy-Item .env.example .env
docker compose up --build
```

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Postgres: `localhost:5432`

Production-сборка:

```powershell
docker compose -f docker-compose.prod.yml up --build -d
```

## Dev/Prod поток через GitHub

Есть workflow: `.github/workflows/docker-images.yml`

- push в `develop` -> публикуются образы с тегами `dev` и `dev-<sha>`
- push тега `v*` (например `v1.0.0`) -> публикуются теги версии и `latest`

Это дает схему:

- локально разрабатываешь;
- push в `develop` -> обновляется dev-образ;
- создаешь git tag -> обновляется prod-образ.

## Структура проекта

- `backend/` — Django API и бизнес-логика
- `frontend/` — Vue/Vite клиент
- `docker-compose.yml` — dev-окружение
- `docker-compose.prod.yml` — production-окружение
- `.github/workflows/docker-images.yml` — CI/CD для Docker-образов

## Важно

В текущем окружении Codex у меня не было доступного `npm` в PATH, поэтому я подготовил полноценный `frontend/package.json`, конфиги и исходники, но не смог локально выполнить `npm install && npm run build` именно в этом окружении. На твоем ПК (или в Docker) это запускается штатно.
