# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from pathlib import Path

__all__ = [
    "os",
    "BASE_DIR",
    "PROJECT_DIR",
    "MEDIA_ROOT",
    "STATIC_ROOT",
    "STATICFILES_DIRS",
    "DEBUG",
    "TEMPLATES",
    "INSTALLED_APPS",
    "MIDDLEWARE",
    "CRON_CLASSES",
    "DJANGO_CRON_DELETE_LOGS_OLDER_THAN",
    "ROOT_URLCONF",
    "WSGI_APPLICATION",
    "ORGANIZATION_NAME",
    "ORGANIZATION_SHORT_NAME",
    "ORGANIZATION_LEGAL_NAME",
    "ORGANIZATION_KVK",
    "ORGANIZATION_EMAIL",
    "ORGANIZATION_SUPPLIER_EMAIL",
    "ORGANIZATION_WEBSITE",
    "LANGUAGE_CODE",
    "TIME_ZONE",
    "USE_I18N",
    "USE_L10N",
    "USE_TZ",
    "DECIMAL_SEPARATOR",
    "DATETIME_FORMAT",
    "STATIC_URL",
    "AUTH_USER_MODEL",
    "MEMBER_FEE",
    "LOGIN_REDIRECT_URL",
    "DEFAULT_AUTO_FIELD",
    "EMAIL_SUBJECT_PREFIX",
    "TEST_RUNNER",
    "MOLLIE_API_KEY",
    "BASE_URL",
    "DEFAULT_FROM_EMAIL",
    "TINYMCE_DEFAULT_CONFIG",
    "HIJACK_ALLOW_GET_REQUESTS",
    "HIJACK_DISPLAY_ADMIN_BUTTON",
    "HIJACK_REGISTER_ADMIN",
    "RECAPTCHA_PUBLIC_KEY",
    "RECAPTCHA_PRIVATE_KEY",
    "NOCAPTCHA",
    "CAPTCHA_ENABLED",
    "CONSTANCE_BACKEND",
    "CONSTANCE_CONFIG",
    "CONSTANCE_CONFIG_FIELDSETS",
    "LOGGING",
]

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_DIR = Path(__file__).parent.parent.parent
MEDIA_ROOT = PROJECT_DIR / "media"
STATIC_ROOT = PROJECT_DIR / "static"
STATICFILES_DIRS = (PROJECT_DIR / "assets",)

DEBUG = False

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(os.path.dirname(BASE_DIR), "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "ordering.context_processors.pickup_locations",
                "vokou.context_processors.organization",
            ],
        },
    },
]


# Application definition

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_nose",
    "tinymce",
    "django_extensions",
    "braces",
    "django_bootstrap5",
    "django_cron",
    "captcha",
    "mailing",
    "accounts",
    "log",
    "finance",
    "ordering",
    "docs",
    "transport",
    "api",
    "distribution",
    "groups",
    "agenda",
    "news",
    "constance.backends.database",
    "constance",
    "hijack",
    "hijack.contrib.admin",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.common.BrokenLinkEmailsMiddleware",
    "vokou.middleware.OrderRoundMiddleware",
    "hijack.middleware.HijackUserMiddleware",
]

CRON_CLASSES = [
    "ordering.cron.MailOrderLists",
    "ordering.cron.SendOrderReminders",
    "ordering.cron.SendPickupReminders",
    "ordering.cron.SendRideMails",
    "ordering.cron.SendPrepareRideMails",
    "ordering.cron.SendDistributionMails",
    "ordering.cron.SendRideCostsRequestMails",
    "ordering.cron.AutoCreateOrderRoundBatch",
]

DJANGO_CRON_DELETE_LOGS_OLDER_THAN = 365

ROOT_URLCONF = "vokou.urls"
WSGI_APPLICATION = "vokou.wsgi.application"

# Organization-specific settings (from environment, with VOKO Utrecht defaults)
ORGANIZATION_NAME = os.environ.get("ORGANIZATION_NAME", "VOKO Utrecht")
ORGANIZATION_SHORT_NAME = os.environ.get("ORGANIZATION_SHORT_NAME", "VOKO Utrecht")
ORGANIZATION_LEGAL_NAME = os.environ.get(
    "ORGANIZATION_LEGAL_NAME", "Stichting Financiën VOKO Utrecht"
)
ORGANIZATION_KVK = os.environ.get("ORGANIZATION_KVK", "61879584")
ORGANIZATION_EMAIL = os.environ.get("ORGANIZATION_EMAIL", "info@vokoutrecht.nl")
ORGANIZATION_SUPPLIER_EMAIL = os.environ.get(
    "ORGANIZATION_SUPPLIER_EMAIL", "boeren@vokoutrecht.nl"
)
ORGANIZATION_WEBSITE = os.environ.get(
    "ORGANIZATION_WEBSITE", "https://www.vokoutrecht.nl"
)

# Internationalization

LANGUAGE_CODE = "nl-nl"
TIME_ZONE = "Europe/Amsterdam"
USE_I18N = True
USE_L10N = False
USE_TZ = True
DECIMAL_SEPARATOR = ","
DATETIME_FORMAT = "j F Y, H:i"

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"

AUTH_USER_MODEL = "accounts.VokoUser"
MEMBER_FEE = 20.0
LOGIN_REDIRECT_URL = "/"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

EMAIL_SUBJECT_PREFIX = "[Voko Admin] "

TEST_RUNNER = "django_nose.NoseTestSuiteRunner"

MOLLIE_API_KEY = os.environ.get("MOLLIE_API_KEY", "SETME")

BASE_URL = os.environ.get("BASE_URL", "https://leden.vokoutrecht.nl")
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", "VOKO Utrecht <info@vokoutrecht.nl>"
)

TINYMCE_DEFAULT_CONFIG = {
    "plugins": "table,xhtmlxtras,paste,searchreplace",
    "theme_advanced_buttons3_add": "cite,abbr",
    "cleanup_on_startup": True,
    "custom_undo_redo_levels": 10,
    "forced_root_block": False,
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


CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"

CONSTANCE_CONFIG = {
    # templates
    "ACTIVATE_ACCOUNT_MAIL": (1, "Activate account mail", int),
    "CONFIRM_MAIL": (2, "Confirm account mail", int),
    "ORDER_REMINDER_MAIL": (4, "Order reminder mail", int),
    "PASSWORD_RESET_MAIL": (9, "Password reset mail", int),
    "ORDER_CONFIRM_MAIL": (12, "Order confirm mail", int),
    "ORDER_FAILED_MAIL": (37, "Order failed mail", int),
    "RIDE_MAIL": (84, "Ride info mail", int),
    "PREPARE_RIDE_MAIL": (85, "Prepare ride info mail", int),
    "DISTRIBUTION_MAIL": (84, "Distribution info mail", int),
    "PICKUP_REMINDER_MAIL": (107, "Order pickup reminder mail", int),
    "RIDECOSTS_REQUEST_MAIL": (108, "Ride costs request mail", int),
    # group ids
    "ADMIN_GROUP": (1, "Admin Group", int),
    "TRANSPORT_GROUP": (2, "Transport Group", int),
    "DISTRIBUTION_GROUP": (3, "Distribution Group", int),
    "FARMERS_GROUP": (5, "Farmers Group", int),
    "IT_GROUP": (4, "IT Group", int),
    "PROMO_GROUP": (7, "Promotion Group", int),
    "FINANCE_GROUP": (9, "Finance Group", int),
    # other config values
    "MARKUP_PERCENTAGE": (4.0, "Markup percentage", float),
    "UNSUBSCRIBE_FORM_URL": ("", "Unsubscribe form URL", str),
    # automated orderround creation
    "AUTO_CREATE_ORDERROUNDS": (False, "Automatically create new order rounds", bool),
    "ORDERROUND_OPEN_DAY_OF_WEEK": (
        6,
        "Day of week when order rounds open (0=Monday, 6=Sunday). Follows Python's datetime.weekday() convention.",
        int,
    ),
    "ORDERROUND_CREATE_DAYS_AHEAD": (
        31,
        "Days in advance to create order round batch",
        int,
    ),
    "ORDERROUND_INTERVAL_WEEKS": (2, "Interval between order rounds in weeks", int),
    "ORDERROUND_OPEN_HOUR": (12, "Hour when order rounds open (24h format)", int),
    "ORDERROUND_DURATION_HOURS": (63, "How long order rounds stay open (hours)", int),
    "ORDERROUND_COLLECT_DAYS_AFTER": (
        0,
        "Days after closing when products can be collected",
        int,
    ),
    "ORDERROUND_COLLECT_HOUR": (
        18,
        "Hour when products can be collected (24h format)",
        int,
    ),
    "ORDERROUND_TRANSPORT_COORDINATOR": (
        986,
        "Default transport coordinator user ID",
        int,
    ),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "General Options": (
        "ACTIVATE_ACCOUNT_MAIL",
        "CONFIRM_MAIL",
        "ORDER_REMINDER_MAIL",
        "PASSWORD_RESET_MAIL",
        "ORDER_CONFIRM_MAIL",
        "ORDER_FAILED_MAIL",
        "RIDE_MAIL",
        "PREPARE_RIDE_MAIL",
        "DISTRIBUTION_MAIL",
        "PICKUP_REMINDER_MAIL",
        "RIDECOSTS_REQUEST_MAIL",
    ),
    "Group Ids": (
        "TRANSPORT_GROUP",
        "DISTRIBUTION_GROUP",
        "ADMIN_GROUP",
        "FARMERS_GROUP",
        "IT_GROUP",
        "PROMO_GROUP",
        "FINANCE_GROUP",
    ),
    "Order Round Automation": (
        "AUTO_CREATE_ORDERROUNDS",
        "ORDERROUND_CREATE_DAYS_AHEAD",
        "ORDERROUND_OPEN_DAY_OF_WEEK",
        "ORDERROUND_INTERVAL_WEEKS",
        "ORDERROUND_OPEN_HOUR",
        "ORDERROUND_DURATION_HOURS",
        "ORDERROUND_COLLECT_DAYS_AFTER",
        "ORDERROUND_COLLECT_HOUR",
        "ORDERROUND_TRANSPORT_COORDINATOR",
    ),
    "Other options": ("MARKUP_PERCENTAGE", "UNSUBSCRIBE_FORM_URL"),
}


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}
