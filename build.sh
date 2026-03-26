#!/usr/bin/env bash
# Salir si hay algún error
set -o errexit

echo "Instalando dependencias..."
pip install -r requirements.txt

echo "Recolectando estáticos..."
python manage.py collectstatic --no-input

echo "Aplicando migraciones a PostgreSQL..."
python manage.py migrate

echo "Cargando backup definitivo..."
python manage.py loaddata backup_final.json

# Bloque para crear el superusuario automáticamente sin consola
if [[ -n "${DJANGO_SUPERUSER_USERNAME}" ]] && [[ -n "${DJANGO_SUPERUSER_PASSWORD}" ]] && [[ -n "${DJANGO_SUPERUSER_EMAIL}" ]]; then
  echo "Creando superusuario..."
  python manage.py createsuperuser --noinput || true
fi