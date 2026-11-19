"""Cấu hình dùng chung; thông tin riêng được đọc từ tệp .env."""
from pathlib import Path

from decouple import Config, Csv, RepositoryEnv
from django.contrib.messages import constants as message_constants

BASE_DIR = Path(__file__).resolve().parent.parent
env_file = BASE_DIR / ".env"
env = Config(RepositoryEnv(str(env_file))) if env_file.exists() else Config()
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = env("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "accounts.apps.AccountsConfig", "catalog.apps.CatalogConfig",
    "customers.apps.CustomersConfig", "bookings.apps.BookingsConfig",
    "operations.apps.OperationsConfig", "reports.apps.ReportsConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "accounts.context_processors.current_role",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DATABASES = {"default": {
    "ENGINE": "django.db.backends.mysql",
    "NAME": env("DB_NAME", default="tourmanager"),
    "USER": env("DB_USER", default="tourmanager"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST", default="127.0.0.1"),
    "PORT": env("DB_PORT", default="3306", cast=int),
    "OPTIONS": {"charset": "utf8mb4", "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"},
    "TEST": {"CHARSET": "utf8mb4"},
}}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"
MESSAGE_TAGS = {message_constants.ERROR: "danger"}
