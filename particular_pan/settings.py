from .base_settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['retiros.pan.com.ar']


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_ROOT = BASE_DIR / 'static'
MEDIA_ROOT = BASE_DIR / 'media'
SITE_URL = 'retiros.pan.com.ar'
MEDIA_URL = '/media/'
STATIC_URL = '/static/'


# Recaptcha
RECAPTCHA_PROJECT_ID = ''
RECAPTCHA_SITE_KEY = ''

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.mandrillapp.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'corporativos@pan.com.ar'
EMAIL_HOST_PASSWORD = 'md-esE0YSGhJAk7vfUbIwiXmQ'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'PAN Seguros <corporativos@pan.com.ar>'

EMAIL_CONTACT_CORPORATIVO = 'corporativos@pan.com.ar'
EMAIL_CONSULT = 'info@pan.com.ar'