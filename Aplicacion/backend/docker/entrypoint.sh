#!/bin/bash
set -e

# La credencial de la base de datos NO tiene valor por defecto (A0-VER03-05).
# Si el despliegue no la inyecta, el arranque ABORTA aquí y de forma visible,
# en vez de sondear con una contraseña conocida por cualquiera.
if [ -z "${DB_PASSWORD:-}" ]; then
    echo "ERROR: DB_PASSWORD is required (no default value). Export it or set it in the deployment .env." >&2
    exit 1
fi

echo "Waiting for database to be ready..."
# Wait for db to be truly ready using env vars (DB_*).
# La contraseña se lee del ENTORNO del proceso, nunca se interpola en el
# código: así no aparece en la línea de comandos (visible con `ps`).
until uv run python -c "import os, psycopg2; psycopg2.connect(host=os.environ.get('DB_HOST', 'db'), user=os.environ.get('DB_USER', 'salesianos_user'), password=os.environ['DB_PASSWORD'], dbname=os.environ.get('DB_NAME', 'salesianos_db'))" 2>/dev/null; do
    echo "Database is unavailable - sleeping"
    sleep 2
done

echo "Database is ready!"

echo "Running migrations..."
uv run python manage.py migrate --noinput

echo "Preparing the media volume..."
# `MEDIA_ROOT` es un VOLUMEN PERSISTENTE (FREEZE-MD-1.0.0 · FR-06 §2.1): guarda
# estado durable de negocio, no es un caché. El volumen puede haber sido creado
# por root en una corrida anterior, así que se corrige el dueño ANTES de que
# gunicorn arranque como `appuser`.
#
# El servidor de archivos del despliegue (nginx) lo monta en SÓLO-LECTURA, así
# que el grupo y los demás necesitan LEER: 0755 en directorios y 0644 en
# archivos. Nunca se borra ni se trunca el volumen.
MEDIA_DIR="${MEDIA_ROOT:-/app/media}"
mkdir -p "$MEDIA_DIR"
chown -R appuser:appuser "$MEDIA_DIR" 2>/dev/null || true
chmod -R u+rwX,g+rX,o+rX "$MEDIA_DIR" 2>/dev/null || true

echo "Collecting static files..."
# Fix ownership of staticfiles volume (may have been created by root in previous runs)
chown -R appuser:appuser /app/staticfiles 2>/dev/null || true
uv run python manage.py collectstatic --noinput

echo "Starting server..."
# Daphne is the ASGI server for both HTTP and public WebSocket connections.
exec gosu appuser uv run daphne -b 0.0.0.0 -p 8000 --ping-interval 20 config.asgi:application
