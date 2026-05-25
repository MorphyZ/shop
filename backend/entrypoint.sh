#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput || true

if [ "${LOAD_DEMO_DATA}" = "1" ]; then
  python manage.py seed_demo || true
fi

exec "$@"
