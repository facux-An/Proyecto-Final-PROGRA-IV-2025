# biblioteca_plus/settings.py
import os
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path
import dj_database_url
from django.contrib.messages import constants as messages
import cloudinary
cloudinary.config(
    cloud_name="dsaqqwbdn",
    api_key="967594418321858",
    api_secret="jBjqm0rWf0e_Pup4aOtaVDtZB0o",
    secure=True
)
# Paths
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------------
# Core settings
# -----------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "clave-insegura-para-dev")

DEBUG = os.getenv("DEBUG", "False").strip().lower() == "true"

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "proyecto-final-progra-iv-2025.onrender.com"
).split(",")

CSRF_TRUSTED_ORIGINS = [
    "https://proyecto-final-progra-iv-2025.onrender.com",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
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

    # Apps del proyecto
    
    "ventas",
    "categorias",
    "productos",
    "usuarios",
    
    # Cloudinary
    "cloudinary",
    "cloudinary_storage",
]

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
        "DIRS": [BASE_DIR / "biblioteca_plus" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
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
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")

DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
    )
}

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
    print(f"[Cloudinary] Activado. Carpeta: {CLOUDINARY_FOLDER}")
else:
    # Fallback a disco local
    from django.core.files.storage import FileSystemStorage
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"
    print("[Cloudinary] Desactivado. Usando FileSystemStorage local.")
