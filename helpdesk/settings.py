import os

import dj_database_url
from django.contrib.messages import constants as messages
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.run.app']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tickets',
    'users',
    'company',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Archivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'helpdesk.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'company.context_processors.company_info',
            ],
        },
    },
]

WSGI_APPLICATION = 'helpdesk.wsgi.application'


# Base de datos
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
# En desarrollo se usa DATABASE_TEST; en producción DATABASE_URL.
# Se evita que una variable DATABASE_URL presente en local conecte silenciosamente a producción.

if DEBUG:
    db_url = config('DATABASE_TEST', default=None)
else:
    db_url = config('DATABASE_URL', default=None)

if db_url:
    DATABASES = {
        'default': dj_database_url.parse(
            db_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

CONN_MAX_AGE = 600
CONN_HEALTH_CHECKS = True


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'es'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

LOGIN_REDIRECT_URL = '/dashboard/'

LOGOUT_REDIRECT_URL = '/login/'

LOGIN_URL = '/login/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

# MEDIA_URL = config('MEDIA_URL')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('MAIL_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@localhost')
# Email de soporte técnico
SUPPORT_EMAIL = config('SUPPORT_EMAIL', default=None)

# URL pública del sitio para construir enlaces absolutos en correos
SITE_URL = config('SITE_URL', default='')

AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default=None)
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default=None)
AWS_STORAGE_BUCKET_NAME = config('BUCKET', default=None)
AWS_S3_REGION_NAME = config('REGION_NAME', default=None)
REGION_NAME = config('REGION_NAME', default=None)
AWS_S3_CUSTOM_DOMAIN = config('AWS_S3_CUSTOM_DOMAIN', default=None)

# Configuración de STORAGES
if not DEBUG and AWS_STORAGE_BUCKET_NAME:
    STORAGES = {
        "default": {
            "BACKEND": "helpdesk.storages.MediaStore",
            "OPTIONS": {
                "file_overwrite": False,
                "custom_domain": AWS_S3_CUSTOM_DOMAIN,
            },
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

# Si estamos en producción y tenemos S3, usamos la URL de S3/CloudFront
if not DEBUG and AWS_S3_CUSTOM_DOMAIN:
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
else:
    # En desarrollo usamos la URL de medios local
    MEDIA_URL = '/media/'

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'https://*.run.app',
]

# Elimina campos irrelevantes de la Lista de Mensajes Flash y alinea con Bootstrap 5.
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Seguridad de transporte y cookies
# Se activan automáticamente cuando DEBUG=False, permitiendo sobreescribir por env si es necesario.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=not DEBUG, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=not DEBUG, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=not DEBUG, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=0 if DEBUG else 31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
