# АСУ «Магазин» (Django + Vue + PostgreSQL)

Проект настроен под GitLab и Docker-структуру в стиле твоего примера из `D:\primer`.

## Git

- Основной remote: `origin` -> `https://gitlab.flexidev.ru/shop-kurs/shop.git`
- Резервный remote: `github` -> старый GitHub
- Рабочая ветка: только `main`
- Ветка `develop` удалена локально и на GitLab

Проверка:

```powershell
git remote -v
git branch -vv
```

## Docker-структура (как в примере)

В проекте теперь есть:

- `docker-compose.dev.yml`
- `docker-compose.prod.yml`
- `.gitlab-ci.yml`
- `.ci/deploy.gitlab-ci.yml`
- `conf.dev/nginx.conf`
- `conf.prod/nginx.conf`

И важный момент:

- `docker-compose.yml` удален специально, чтобы не было путаницы.

## Быстрый запуск без Docker

```powershell
cd D:\Kurs
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
powershell -ExecutionPolicy Bypass -File .\scripts\setup_postgres.ps1
.\.venv\Scripts\python backend\manage.py migrate
.\.venv\Scripts\python backend\manage.py seed_demo
.\.venv\Scripts\python backend\manage.py runserver 127.0.0.1:8000
```

Во втором терминале:

```powershell
cd D:\Kurs\frontend
npm install
npm run dev
```

## Docker запуск (dev)

```powershell
cd D:\Kurs
docker compose -f docker-compose.dev.yml up --build
```

Открывать:

- `http://localhost:8005`

## Docker запуск (prod)

```powershell
cd D:\Kurs
docker compose -f docker-compose.prod.yml up --build -d
```

Открывать:

- `http://localhost`

## Как устроены compose-файлы

### `docker-compose.dev.yml`

- `db` (PostgreSQL)
- `backend` (Django runserver)
- `frontend` (Vite dev server)
- `nginx` (прокси на frontend/backend, порт `8005`)

### `docker-compose.prod.yml`

- `db` (PostgreSQL)
- `backend` (gunicorn)
- `frontend` (собранный frontend на nginx внутри контейнера)
- `nginx` (внешний reverse proxy, порт `80`)

## GitLab CI/CD

Файлы:

- `.gitlab-ci.yml` — сборка Docker-образов backend/frontend
- `.ci/deploy.gitlab-ci.yml` — шаблон деплоя на сервер по SSH

Триггеры pipeline:

- Push в `main` -> build job
- Тег `v*` (например `v1.0.0`) -> release/build режим

## Что нужно заполнить в GitLab Variables для deploy

Для job `deploy` нужны переменные:

- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_PATH`
- `SSH_PRIVATE_KEY` (masked/protected)

Без этих переменных deploy job не выполнится.

## Роли в системе

Демо-пользователи:

- `admin / admin12345`
- `operator / user12345`

`admin`:
- полное редактирование данных;
- закупки/оприходование;
- изменение остатков/цен;
- управление отделами.

`operator`:
- просмотр данных;
- создание продаж;
- без админ-операций.

## Изменение остатков товара на базе

Самый простой способ:

1. Войти в `http://127.0.0.1:8000/admin/` как `admin`
2. Открыть `Base stocks`
3. Изменить `quantity` и `purchase_price` прямо в списке
4. Нажать `Save`

## Примечание по безопасности

Рекомендуется сменить пароль GitLab, который был отправлен в чат, и использовать Personal Access Token для Git-операций.