"""
Django settings for config project.
Optimized for AWS Lightsail / Docker Deployment.
"""
from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SEGURIDAD CRÍTICA ---
# En producción, leer desde variables de entorno. En local, usar clave por defecto.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-dev-key-change-in-prod-12345')

# DEBUG: True en tu PC, False en el servidor real
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*'] # Permitir todos los hosts (útil para Docker/Nube)


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis', # GeoDjango (PostGIS)
    'core',               # Tu aplicación principal
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Gestión eficiente de estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'core/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# --- BASE DE DATOS (POSTGIS) ---
# dj_database_url lee la variable DATABASE_URL o usa la default local
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', 'postgis://postgres:supersecreto@db:5432/bomberos_db'),
        conn_max_age=600,         # Mantiene la conexión viva 10 min (Rendimiento)
        ssl_require=not DEBUG     # En producción (AWS RDS) requiere SSL
    )
}
# Forzar el motor PostGIS explícitamente
DATABASES['default']['ENGINE'] = 'django.contrib.gis.db.backends.postgis'


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator' },
]


# Internationalization
LANGUAGE_CODE = 'es-ec'       # Español Ecuador
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True


# --- ARCHIVOS ESTÁTICOS ---
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Dónde buscar tus archivos CSS/JS locales
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Almacenamiento optimizado con compresión (Whitenoise)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- CONTROL DE ACCESO ---
LOGIN_REDIRECT_URL = 'home_ciudadano' 
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'login'


# ==============================================================================
#                       CONFIGURACIÓN DE NOTIFICACIONES
# ==============================================================================

# EMAIL:
# En DESARROLLO (Tu PC): Imprime en la terminal (Gratis, sin errores de clave).
# En PRODUCCIÓN (AWS): Usa Amazon SES automáticamente.
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django_ses.SESBackend'
    AWS_SES_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SES_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_SES_REGION_NAME = os.environ.get('AWS_REGION', 'us-east-1')

DEFAULT_FROM_EMAIL = 'Cuerpo de Bomberos Tulcán <notificaciones@bomberostulcan.gob.ec>'

# SMS (AWS SNS):
# Las credenciales se toman de variables de entorno en producción.
# En local, el código en utils.py hará una simulación si no encuentra las claves.
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
AWS_REGION = 'us-east-1'


# ==============================================================================
#                      SEGURIDAD (ISO 27001 / OWASP)
# ==============================================================================
# Estas reglas solo se activan cuando subas el proyecto a la nube (DEBUG=False)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True