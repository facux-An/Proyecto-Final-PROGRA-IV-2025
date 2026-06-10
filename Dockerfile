FROM python:3.10-slim

WORKDIR /code

# Variables de entorno para Python (optimizaciones)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instalar dependencias del sistema operativo (necesarias para psycopg2)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código del proyecto
COPY . /code/

# ⚠️ LA SOLUCIÓN AL ERROR:
# Le pasamos una URL de Cloudinary falsa SOLO durante la compilación.
# Así collectstatic puede ejecutarse sin pedir la contraseña real.
# La real la vas a poner vos en la sección "Secrets" del panel de Fly.io.
RUN CLOUDINARY_URL="cloudinary://dummy:dummy@dummy" python manage.py collectstatic --noinput

# Arrancar Gunicorn usando la configuración optimizada que hicimos hoy
CMD ["gunicorn", "biblioteca_plus.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4"]
