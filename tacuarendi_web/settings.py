"""
Django settings for tacuarendi_web project.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# CONFIGURACIÓN DE SEGURIDAD (DINÁMICA)
# ==============================================================================

# Si existe una llave secreta en el servidor, la usa. Si no, usa la de desarrollo.
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-ii@9fxxek!3v-kx*9smmr#(g56dx#=r)k+z3135o!e@$kfckg2')

# DEBUG se desactiva solo si detecta que estamos en un servidor de producción (Render o PythonAnywhere)
DEBUG = 'RENDER' not in os.environ and 'PYTHONANYWHERE_DOMAIN' not in os.environ

# Permitimos cualquier host para evitar errores de dominio al desplegar
ALLOWED_HOSTS = ['*']

# Configuración necesaria para formularios en servidores seguros (HTTPS)
if not DEBUG:
    CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com', 'https://*.pythonanywhere.com']


# Application definition

INSTALLED_APPS = [
    # 1. Jazzmin debe ir ANTES de admin para que tome el estilo
    'jazzmin',
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Librerías PRO
    'ckeditor',      # Editor de texto rico
    'django_cleanup.apps.CleanupConfig', # Limpieza automática de archivos viejos
    
    # Mis apps
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # <--- Recomendado para servir estáticos en prod
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tacuarendi_web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Asegura que busque templates globales si los hubiera
        'APP_DIRS': True, # Esto busca dentro de core/templates/
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

WSGI_APPLICATION = 'tacuarendi_web.wsgi.application'


# Database
# Por defecto SQLite. En producción (Render) se suele cambiar a PostgreSQL, 
# pero SQLite funciona bien para sitios institucionales con tráfico moderado.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# Internationalization
LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True


# ==============================================================================
# ARCHIVOS ESTÁTICOS Y MEDIA (CRÍTICO PARA DEPLOY)
# ==============================================================================

# URL pública para acceder a los estáticos
STATIC_URL = 'static/'

# Dónde busca Django los archivos estáticos en desarrollo
STATICFILES_DIRS = [BASE_DIR / 'static'] 

# Dónde recopila Django TODOS los estáticos para producción (comando collectstatic)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Archivos subidos por el usuario (Fotos de obras, noticias)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Motor de almacenamiento para estáticos (WhiteNoise ayuda a servir en prod)
# Si no instalaste whitenoise aun, Django usará el default, pero es buena práctica tenerlo listo.
if not DEBUG:
    try:
        import whitenoise
        STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    except ImportError:
        pass # Si no está instalado whitenoise, usa el default


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==========================================
# CONFIGURACIÓN LOGIN / LOGOUT
# ==========================================
# Cuando te logueas, vas al panel de gestión
LOGIN_REDIRECT_URL = 'gestion_reclamo_list' 
# Cuando salís, volvés al inicio
LOGOUT_REDIRECT_URL = 'home'


# ==========================================
# CONFIGURACIÓN JAZZMIN (ADMINISTRADOR PRO)
# ==========================================

JAZZMIN_SETTINGS = {
    "site_title": "Panel Tacuarendí",
    "site_header": "Gestión Comunal",
    "site_brand": "Tacuarendí Admin",
    "site_logo": "core/img/logo.png",
    "login_logo": "core/img/logo.png",
    "login_logo_dark": None,
    "site_logo_classes": "img-circle",
    "site_icon": None,
    "welcome_sign": "Bienvenido al Panel de Gestión",
    "copyright": "Comuna de Tacuarendí",
    "search_model": "core.Reclamo",

    # Menú lateral con Iconos
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        
        "core.Autoridad": "fas fa-user-tie",
        "core.Obra": "fas fa-hard-hat",
        "core.Tramite": "fas fa-file-signature",
        "core.Documento": "fas fa-file-contract",
        "core.Servicio": "fas fa-address-book",
        "core.Historia": "fas fa-book-open",
        
        "core.Reclamo": "fas fa-bullhorn",
        "core.Secretaria": "fas fa-building",
        "core.Sugerencia": "fas fa-lightbulb",
        "core.InfoCategoria": "fas fa-info-circle",
        
        "core.Novedad": "fas fa-newspaper",
        "core.CategoriaNovedad": "fas fa-tags",
    },
    
    "order_with_respect_to": [
        "core.Reclamo", 
        "core.Sugerencia", 
        "core.Novedad",
        "core.Obra", 
        "core.Tramite"
    ],
    "show_ui_builder": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-success",
    "accent": "accent-success",
    "navbar": "navbar-success navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-light-success",
    "sidebar_nav_small_text": False,
    "theme": "flatly", 
    "button_classes": {
        "primary": "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

# Configuración CKEditor (FIX SEGURIDAD APLICADO)
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink'],
            ['RemoveFormat', 'Source']
        ],
        'width': '100%',
        'height': 300,
        'versionCheck': False,  # <--- ESTO ELIMINA EL ERROR ROJO
    }
}