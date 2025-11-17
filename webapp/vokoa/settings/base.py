# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from pathlib import Path


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_DIR = Path(__file__).parent.parent.parent
MEDIA_ROOT = PROJECT_DIR / "media"
STATIC_ROOT = PROJECT_DIR / "static"
STATICFILES_DIRS = (
    PROJECT_DIR / "assets",
)

DEBUG = False

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'ordering.context_processors.pickup_locations'
            ],
        },
    },
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_nose',
    'tinymce',
    'django_extensions',
    'braces',
    'django_bootstrap5',
    "django_cron",
    "captcha",

    'mailing',
    'accounts',
    'log',
    'finance',
    'ordering',
    'docs',
    'transport',
    'api',
    'distribution',
    'groups',
    'agenda',

    'constance.backends.database',
    'constance',

    'hijack',
    'hijack.contrib.admin',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware',
    'vokou.middleware.OrderRoundMiddleware',
    'hijack.middleware.HijackUserMiddleware',
]

CRON_CLASSES = [
    "ordering.cron.MailOrderLists",
    "ordering.cron.SendOrderReminders",
    "ordering.cron.SendPickupReminders",
    "ordering.cron.SendRideMails",
    "ordering.cron.SendPrepareRideMails",
    "ordering.cron.SendDistributionMails",
    "ordering.cron.SendRideCostsRequestMails"
]

DJANGO_CRON_DELETE_LOGS_OLDER_THAN = 365

ROOT_URLCONF = 'vokou.urls'
WSGI_APPLICATION = 'vokoa.wsgi.application'

# Internationalization

LANGUAGE_CODE = 'nl-nl'
TIME_ZONE = 'Europe/Amsterdam'
USE_I18N = True
USE_L10N = False
USE_TZ = True
DECIMAL_SEPARATOR = ','
DATETIME_FORMAT = "j F Y, H:i"

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

AUTH_USER_MODEL = "accounts.VokoUser"
MEMBER_FEE = 20.0
LOGIN_REDIRECT_URL = "/"

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

EMAIL_SUBJECT_PREFIX = "[Voko Admin] "

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

MOLLIE_API_KEY = "SETME"

BASE_URL = "https://leden.voedselkollektief.nl"
DEFAULT_FROM_EMAIL = "Voedselkollektief Amersfoort <info@voedselkollektief.nl>"

TINYMCE_DEFAULT_CONFIG = {
    'plugins': "table,xhtmlxtras,paste,searchreplace",
    "theme_advanced_buttons3_add" : "cite,abbr",
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 10,
    'forced_root_block': False,
    "width": "75%",
    "height": "500px",
}

HIJACK_ALLOW_GET_REQUESTS = True
HIJACK_DISPLAY_ADMIN_BUTTON = False  # Because of custom user model
HIJACK_REGISTER_ADMIN = False  # Because of custom user model

RECAPTCHA_PUBLIC_KEY = os.getenv("RECAPTCHA_SITE_KEY")
RECAPTCHA_PRIVATE_KEY = os.getenv("RECAPTCHA_SECRET_KEY")
NOCAPTCHA = True
CAPTCHA_ENABLED = True


CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'

CONSTANCE_CONFIG = {
    # templates
    'ACTIVATE_ACCOUNT_MAIL': (1, "Activate account mail", int),
    'CONFIRM_MAIL': (2, "Confirm account mail", int),
    'ORDER_REMINDER_MAIL': (4, "Order reminder mail", int),
    'PASSWORD_RESET_MAIL': (9, "Password reset mail", int),
    'ORDER_CONFIRM_MAIL': (12, "Order confirm mail", int),
    'ORDER_FAILED_MAIL': (37, "Order failed mail", int),
    'RIDE_MAIL': (84, "Ride info mail", int),
    'PREPARE_RIDE_MAIL': (85, "Prepare ride info mail", int),
    'DISTRIBUTION_MAIL': (84, "Distribution info mail", int),
    'PICKUP_REMINDER_MAIL': (107, "Order pickup reminder mail", int),
    'RIDECOSTS_REQUEST_MAIL': (108, "Ride costs request mail", int),
    # group ids

    'ADMIN_GROUP': (1, "Admin Group" , int),
    'TRANSPORT_GROUP': (2, "Transport Group", int),
    'DISTRIBUTION_GROUP': (3, "Distribution Group", int),
    'FARMERS_GROUP': (5, "Farmers Group", int),
    'IT_GROUP': (4, "IT Group", int),
    'PROMO_GROUP': (7, "Promotion Group", int),
    'FINANCE_GROUP': (9, "Finance Group", int),
    # other config values
    'MARKUP_PERCENTAGE': (4.0, "Markup percentage", float),
    'UNSUBSCRIBE_FORM_URL': ("", "Unsubscribe form URL", str)
    
}

CONSTANCE_CONFIG_FIELDSETS = {
        'General Options': (
            'ACTIVATE_ACCOUNT_MAIL',
            'CONFIRM_MAIL',
            'ORDER_REMINDER_MAIL',
            'PASSWORD_RESET_MAIL',
            'ORDER_CONFIRM_MAIL',
            'ORDER_FAILED_MAIL',
            'RIDE_MAIL',
            'PREPARE_RIDE_MAIL',
            'DISTRIBUTION_MAIL',
            'PICKUP_REMINDER_MAIL',
            'RIDECOSTS_REQUEST_MAIL'),
        'Group Ids': (
            'TRANSPORT_GROUP',
            'DISTRIBUTION_GROUP',
            'ADMIN_GROUP',
            'FARMERS_GROUP',
            'IT_GROUP',
            'PROMO_GROUP',
            'FINANCE_GROUP'),
        'Other options': ('MARKUP_PERCENTAGE','UNSUBSCRIBE_FORM_URL')
    }    


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
