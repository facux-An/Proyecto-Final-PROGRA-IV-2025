# biblioteca_plus/settings.py
import os
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path
import dj_database_url
from django.contrib.messages import constants as messages

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------------
# Core settings
# -----------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "clave-insegura-para-dev")

# Seguridad: El modo DEBUG solo es True si la variable en .env dice explícitamente "True".
# En Render, al no existir esta variable (o si la ponés en False), el modo seguro se activa.
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Seguridad: Si el modo DEBUG está en False (Producción), exigimos que haya un ALLOWED_HOSTS
# en las variables de entorno. Si no lo hay, falla rápido para evitar exposición.
if not DEBUG:
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")
else:
    # En desarrollo (DEBUG=True), permitimos local y Render por comodidad
    ALLOWED_HOSTS = ["127.0.0.1", "localhost", "proyecto-final-progra-iv-2025.onrender.com"]

CSRF_TRUSTED_ORIGINS = [
    "https://proyecto-final-progra-iv-2025.onrender.com",
    "https://proyecto-final-progra-iv-2025.fly.dev",
    "https://tiendaplus.com.ar",
    "https://www.tiendaplus.com.ar",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]

# Seguridad de Cookies en Producción (Evita errores de CSRF y State Mismatch con Google OAuth)
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

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

    # Apps del proyecto
    
    "ventas",
    "categorias",
    "productos",
    "usuarios",
    
    # Cloudinary
    "cloudinary",
    "cloudinary_storage",
    
    # django-allauth inicio con google.
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------
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
    # --- Middleware de Allauth inyectado aquí ---
    "allauth.account.middleware.AccountMiddleware",
    # --------------------------------------------
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
        "DIRS": [BASE_DIR / "templates"],
        "OPTIONS": {
            "loaders": [
                (
                    "django.template.loaders.cached.Loader",
                    [
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ],
                ),
            ],
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "ventas.context_processors.carrito_count",
            ],
        },
    },
]

# -----------------------------------------------------------------------------
# Base de datos
# -----------------------------------------------------------------------------
# 1. Definimos la ruta ABSOLUTA para SQLite usando BASE_DIR para que nunca se pierda
ruta_sqlite_local = f"sqlite:///{BASE_DIR / 'db.sqlite3'}"

# 2. Buscamos la variable de entorno, si no está, usamos la ruta local blindada
DATABASE_URL = os.getenv("DATABASE_URL", ruta_sqlite_local)

# 3. Configuramos la conexión
# NOTA: conn_max_age=0 porque usamos el pooler de Neon (PgBouncer).
# PgBouncer ya recicla conexiones por su cuenta. Si Django también las reutiliza
# (conn_max_age=600), se generan errores de "SSL connection closed unexpectedly".
DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=0,
    )
}

# 4. Seguridad SSL obligatoria solo para PostgreSQL en la nube
if DATABASE_URL.startswith(("postgres://", "postgresql://")):
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

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

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
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")
MERCADOPAGO_PUBLIC_KEY = os.getenv("MERCADOPAGO_PUBLIC_KEY", "")
SITE_URL = os.getenv("SITE_URL", "https://proyecto-final-progra-iv-2025.onrender.com")

# Zipnova (ex Zippin) - Motor Logístico
ZIPNOVA_API_TOKEN = os.getenv("ZIPNOVA_API_TOKEN", "")
ZIPNOVA_API_SECRET = os.getenv("ZIPNOVA_API_SECRET", "")
ZIPNOVA_ACCOUNT_ID = os.getenv("ZIPNOVA_ACCOUNT_ID", "")
ZIPNOVA_ORIGIN_ZIPCODE = os.getenv("ZIPNOVA_ORIGIN_ZIPCODE", "1763")

# -----------------------------------------------------------------------------
# Cloudinary (activación segura con flag)
# -----------------------------------------------------------------------------
CLOUDINARY_ENABLED = os.getenv("CLOUDINARY_ENABLED", "False").strip().lower() == "true"
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL", "")
CLOUDINARY_FOLDER = os.getenv("CLOUDINARY_FOLDER", "biblioteca_plus")

if CLOUDINARY_ENABLED and CLOUDINARY_URL:
    # Storage por defecto: Cloudinary
    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
    # Static sigue con Whitenoise; media se sube a Cloudinary
    MEDIA_URL = "/media/"  # (no se usa para servir desde Cloudinary, pero mantiene compatibilidad)
else:
    # Fallback a disco local
    from django.core.files.storage import FileSystemStorage
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"

# -----------------------------------------------------------------------------
# Caché en Memoria (LocMemCache)
# -----------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "tiendaplus-cache",
    }
}

# -----------------------------------------------------------------------------
# Proveedores de Autenticación Social (Allauth)
# -----------------------------------------------------------------------------
# Configuración declarativa para evitar depender de registros en la base de datos (SocialApp)
# y prevenir errores "DoesNotExist" si la base de datos se limpia o migra.
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
            "key": ""  # Requerido por la especificación de allauth (puede estar vacío)
        }
    }
}

