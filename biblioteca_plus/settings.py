# biblioteca_plus/settings.py
import os
from pathlib import Path
import dj_database_url
from django.contrib.messages import constants as messages

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------------
# Core settings
# -----------------------------------------------------------------------------
# Secret key
SECRET_KEY = os.getenv("SECRET_KEY", "clave-insegura-para-dev")

# Debug (usa "True"/"False" en variables de entorno)
DEBUG = os.getenv("DEBUG", "False").strip().lower() == "true"

# Allowed hosts (incluye tu dominio de Render y localhost)
ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "proyecto-final-progra-iv-2025.onrender.com,localhost,127.0.0.1"
).split(",")

# Opcional: protege CSRF en entorno productivo para tu dominio de Render
CSRF_TRUSTED_ORIGINS = [
    "https://proyecto-final-progra-iv-2025.onrender.com",
]

# -----------------------------------------------------------------------------
# Apps
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Apps del proyecto (asegúrate de no duplicarlas)
    "productos.apps.ProductosConfig",
    "ventas",
    "categorias",
    "usuarios",
    'cloudinary',
    'cloudinary_storage',
]

# Archivos multimedia (imágenes de productos)
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'









# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # estáticos en producción
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# -----------------------------------------------------------------------------
# URLs / WSGI
# -----------------------------------------------------------------------------
ROOT_URLCONF = "biblioteca_plus.urls"
WSGI_APPLICATION = "biblioteca_plus.wsgi.application"

# -----------------------------------------------------------------------------
# Templates
# -----------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Tu carpeta de templates principal
        "DIRS": [BASE_DIR / "biblioteca_plus" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Context processor del carrito (tu app ventas)
                "ventas.context_processors.carrito_count",
            ],
        },
    },
]

# -----------------------------------------------------------------------------
# Base de datos
# -----------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")

# Parseo principal (no forzar ssl de forma incondicional)
DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
    )
}

# Solo aplicar SSL si es Postgres (evita el error 'sslmode' con SQLite)
if DATABASE_URL.startswith(("postgres://", "postgresql://")):
    # Algunas plataformas requieren esta opción explícita
    DATABASES["default"].setdefault("OPTIONS", {})
    DATABASES["default"]["OPTIONS"]["sslmode"] = "require"

# -----------------------------------------------------------------------------
# Internacionalización
# -----------------------------------------------------------------------------
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------------
# Archivos estáticos y media
# -----------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# WhiteNoise: compresión y manifest para cache busting en producción
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# -----------------------------------------------------------------------------
# Autenticación
# -----------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"
LOGIN_URL = "login"

# -----------------------------------------------------------------------------
# Mensajes
# -----------------------------------------------------------------------------
MESSAGE_TAGS = {
    messages.DEBUG: "secondary",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "danger",
}

# -----------------------------------------------------------------------------
# Integraciones externas
# -----------------------------------------------------------------------------
# Mercado Pago
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")
