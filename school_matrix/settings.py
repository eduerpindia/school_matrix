import os
from pathlib import Path
from decouple import config
import sys

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '*']

# Multi-tenant DB backend
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',  # ✅ यही रखें
        'NAME': config('DATABASE_NAME'),
        'USER': config('DATABASE_USER'),
        'PASSWORD': config('DATABASE_PASSWORD'),
        'HOST': config('DATABASE_HOST'),
        'PORT': config('DATABASE_PORT'),
    }
}



# Tenant settings
TENANT_MODEL = "schools.School"
TENANT_DOMAIN_MODEL = "schools.Domain"

AUTH_USER_MODEL = "users.User"
SHARED_APPS = [
    'django_tenants',  # must be first
    
    # Django core apps - IMPORTANT ORDER
    'django.contrib.contenttypes',
    'django.contrib.auth',
    
    # Your apps - users MUST come before admin
    'users',  # ✅ FIRST your custom apps
    'schools',  # ✅ THEN your other apps
    
    # Django built-in apps - AFTER your apps
    'django.contrib.admin',  # ❌ This comes AFTER users
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'corsheaders',
]

TENANT_APPS = [
    # Django core apps
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'corsheaders',

    # Your tenant apps
    'users',
    'core',
    'students',
    'teachers',
    'classes',
    'attendance',
    'fees',
    'examinations',
    'library',
    'api',
]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]
MIDDLEWARE = [
    'api.middleware.TenantHeaderMiddleware',  # केवल आपका middleware
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'school_matrix.urls'
# PUBLIC_SCHEMA_URLCONF = 'school_matrix.urls_public'

DATABASE_ROUTERS = ('django_tenants.routers.TenantSyncRouter',)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'api.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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
JWT_SECRET_KEY = config('JWT_SECRET_KEY', default='fallback-secret-key')
JWT_ALGORITHM = config('JWT_ALGORITHM', default='HS512')
JWT_EXPIRATION_DAYS = config('JWT_EXPIRATION_DAYS', default=7, cast=int)

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
CORS_ALLOW_CREDENTIALS = True

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}


TOKEN_EXPIRED_AFTER_SECONDS = 86400 