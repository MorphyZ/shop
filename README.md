# АСУ «Магазин» (Monorepo: backend + frontend)

Проект переведен на GitLab CI/CD и Docker-структуру под монорепозиторий.

## 1. Текущая Docker-структура

В репозитории используются:

- `docker-compose.dev.yml`
- `docker-compose.prod.yml`
- `conf.dev/nginx.conf`
- `conf.prod/nginx.conf`
- `.gitlab-ci.yml`
- `.ci/build.gitlab-ci.yml`
- `.ci/deploy.gitlab-ci.yml`

Файл `docker-compose.yml` намеренно не используется.

## 2. Как устроен CI/CD

### Главный файл

- `.gitlab-ci.yml` подключает твои правила:
  - `workflow.gitlab-ci.yml`
  - `docker.gitlab-ci.yml`
  - `docker-auth.yml`
  - `gitversion-ci-cd-plugin-extension.gitlab-ci.yml`
  - `prepare-settings.yml`
  - `release.gitlab-ci.yml`
  - локальные `.ci/*.gitlab-ci.yml`

### Локальные CI-файлы

- `.ci/build.gitlab-ci.yml`
  - build/push backend image: `$CI_REGISTRY_IMAGE/backend:$DOCKER_TAG`
  - build/push frontend image: `$CI_REGISTRY_IMAGE/frontend:$DOCKER_TAG`

- `.ci/deploy.gitlab-ci.yml`
  - деплой по SSH
  - выбор compose-файла по окружению (`dev`/`prod`)
  - логин в registry на удаленном сервере
  - `docker compose pull` + `docker compose up -d --remove-orphans`

## 3. Используемые CI/CD переменные

Из твоего списка используются:

- `CI_REGISTRY_IMAGE`
- `DEPLOY_HOST` (fallback, если не задан `SSH_HOST`)
- `DEPLOY_PROJECT`
- `SSH_DIR`
- `SSH_HOST`
- `SSH_PORT`
- `SSH_USER`

Дополнительно для deploy нужен:

- `SSH_PRIVATE_KEY`

## 4. Docker Compose (важно)

Оба compose-файла поддерживают и `image`, и `build`:

- В CI/CD и на сервере используется `image` из registry.
- Локально можно запустить даже без registry, через `build`.

## 5. Локальный запуск Docker (dev)

```powershell
cd D:\Kurs
docker compose -f docker-compose.dev.yml up --build
```

Открыть:

- `http://localhost:8005`

## 6. Локальный запуск без Docker

Backend:

```powershell
cd D:\Kurs
.\.venv\Scripts\python backend\manage.py runserver 127.0.0.1:8000
```

Frontend:

```powershell
cd D:\Kurs\frontend
npm run dev
```

Открыть:

- `http://127.0.0.1:5173`

## 7. Деплой через CI

- Push в `main` -> собираются образы.
- Тег `v*` -> release-поток (по твоим правилам workflow).
- Deploy job запускается вручную из GitLab pipeline.

## 8. Git remotes

- `origin` -> GitLab (`https://gitlab.flexidev.ru/shop-kurs/shop.git`)
- `github` -> старый резервный remote

Проверка:

```powershell
git remote -v
git branch -vv
```