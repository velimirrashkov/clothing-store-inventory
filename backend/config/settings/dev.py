from .base import *  # noqa: F401,F403

DEBUG = True
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key")  # noqa: F405
ALLOWED_HOSTS = ["*"]

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
