

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
     #('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'mysql'          
DATABASE_NAME = 'mlgb'            
DATABASE_USER = 'mlgbAdmin'          
DATABASE_PASSWORD = 'blessing'         
DATABASE_HOST = ''            
DATABASE_PORT = ''           

TIME_ZONE = 'Europe/London'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = True

MEDIA_ROOT = '/opt/www/mlgb/media/'

MEDIA_URL = '/feeds/media/'

ADMIN_MEDIA_PREFIX = '/media/'


SECRET_KEY = 'zv&ymi5k&u!eya$bay_bbqb6k*1k-y3h+^28y*d!z*_m7+*x4y'


TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
    
)

ROOT_URLCONF = 'mysite.apache.urls'

TEMPLATE_DIRS = (
    "/opt/www/mlgb/templates",
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.redirects',
    'django.contrib.admin',
    'mysite.books',
    'mysite.mlgb',
    'mysite.feeds',
)
