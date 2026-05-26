# АСУ «Магазин» (Django + Vue + PostgreSQL)

Проект для учета товаров, закупок, продаж и отчетности магазина.

## 1) Быстрый запуск (локально, без Docker)

### Шаг 1. Установка зависимостей

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

Проверь `.env`:

```env
POSTGRES_DB=shop_db
POSTGRES_USER=shop_user
POSTGRES_PASSWORD=shop_pass
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
USE_SQLITE=0
```

### Шаг 3. Подготовка PostgreSQL

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_postgres.ps1
```

### Шаг 4. Миграции и демо-данные

```powershell
.\.venv\Scripts\python backend\manage.py migrate
.\.venv\Scripts\python backend\manage.py seed_demo
```

### Шаг 5. Запуск backend

```powershell
.\.venv\Scripts\python backend\manage.py runserver 127.0.0.1:8000
```

### Шаг 6. Запуск frontend (второй терминал)

```powershell
cd D:\Kurs\frontend
npm install
npm run dev
```

Открыть:
- Frontend: http://127.0.0.1:5173
- Admin: http://127.0.0.1:8000/admin/
- API: http://127.0.0.1:8000/api/

## 2) Роли: `admin` и `operator`

Демо-пользователи:
- `admin / admin12345`
- `operator / user12345`

Что может `admin`:
- Полный доступ на изменение (CRUD) справочников.
- Изменять товары, базы, отделы, остатки.
- Создавать закупки и оприходовать закупку.
- Открывать/закрывать отделы.
- Перемещать товар между отделами.
- Менять цены.

Что может `operator`:
- Читать данные (просмотр API и интерфейса).
- Создавать продажи.

Ограничение `operator`:
- Нельзя изменять справочники и остатки.
- Нельзя оприходовать закупки и выполнять админ-операции.

## 3) Как менять количество товара на базе

Вариант A (рекомендуется, самый простой): через Django Admin
1. Войти как `admin`.
2. Открыть `Base stocks`.
3. В списке можно менять `quantity` и `purchase_price` прямо в таблице.
4. Нажать `Save`.

Вариант B: через API
1. Получить список остатков:
```http
GET /api/base-stocks/
```
2. Изменить конкретный остаток (пример id=5):
```http
PATCH /api/base-stocks/5/
{
  "quantity": 120,
  "purchase_price": "57.50"
}
```

Вариант C: через pgAdmin (SQL)
```sql
UPDATE shop_basestock
SET quantity = 120,
    purchase_price = 57.50
WHERE id = 5;
```

## 4) PDF и кириллица

Если в PDF раньше были квадраты вместо русского текста, это уже исправлено:
- в генерации PDF добавлен выбор Unicode-шрифтов (`Arial/DejaVu`),
- для Docker добавлен пакет `fonts-dejavu-core`.

## 5) Как показать проект на другом компьютере

## Вариант 1 (лучший): через GitHub
1. Установить на новом ПК: Git, Python, Node.js, PostgreSQL.
2. Клонировать проект:
```powershell
git clone https://github.com/MorphyZ/shop.git
cd shop
```
3. Выполнить шаги из раздела «Быстрый запуск».

## Вариант 2: перенос архивом
1. Заархивировать проект (без `.venv` и `frontend/node_modules`).
2. Распаковать на новом ПК.
3. Выполнить шаги из раздела «Быстрый запуск».

## Перенос данных БД (если нужны именно твои данные)
1. На старом ПК в pgAdmin: `shop_db -> Backup`.
2. На новом ПК: создать пустую `shop_db`.
3. В pgAdmin: `shop_db -> Restore` из backup-файла.

## 6) Git flow (dev/prod)

- `main` — основная ветка.
- CI workflow: `.github/workflows/docker-images.yml`
  - push в `main` -> собираются dev-образы,\n  - push тега `v*` -> собираются prod-образы.

Пример релиза:
```powershell
git checkout develop
git checkout main
git merge develop
git push origin main
git tag v1.0.0
git push origin v1.0.0
```

## 7) Частая проблема с «кракозябрами» в терминале

Если русский текст в PowerShell отображается некорректно:
```powershell
chcp 65001
```

И в VS Code выбрать `UTF-8` для файла.
## 8) Переезд с GitHub на GitLab

В проекте уже переключен основной remote на GitLab:

- `origin` -> `https://gitlab.flexidev.ru/shop-kurs/shop.git`
- `github` -> резервный remote со старого GitHub

Проверка:

```powershell
git remote -v
git branch -vv
```

Отправка веток в GitLab:

```powershell
git push origin main
```

Важно по безопасности:

- Для GitLab лучше использовать Personal Access Token вместо пароля.
- Так как пароль уже был отправлен в чат, рекомендуется сменить пароль аккаунта и/или отозвать старые токены.

## 9) Почему у коллег больше файлов в backend/frontend

Это нормально. У коллег другой уровень зрелости проекта и другой стек на фронтенде.

Основные причины отличий:

- У коллег есть отдельные файлы окружений (`.env.development`, `.env.production`).
- Есть отдельные docker-compose для dev/prod (`docker-compose.dev.yml`, `docker-compose.prod.yml`).
- Есть CI для GitLab (`.gitlab-ci.yml`).
- Backend разбит на большее количество Django-приложений и сервисов.
- Во frontend у коллег Quasar-структура (`quasar.config.js`, `boot/`, расширенная `src/`).
- Есть отдельные Nginx-конфиги (`conf.dev`, `conf.prod`) и дополнительные Dockerfile.

У тебя проект проще по структуре, но это не ошибка. Для учебного/демо-показа он уже рабочий.

Если захочешь, следующим шагом можно привести структуру к «прод-стандарту» GitLab:

1. Добавить `.gitlab-ci.yml`.\n2. Добавить `conf.dev/nginx.conf` и `conf.prod/nginx.conf`.\n3. Добавить frontend `.env.development` и `.env.production`.