import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("clothing_store")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "expire-stale-reservations": {
        "task": "apps.inventory.tasks.expire_stale_reservations",
        "schedule": 120.0,
    },
    "reconcile-stock-levels": {
        "task": "apps.inventory.tasks.reconcile_stock_levels",
        "schedule": crontab(hour=3, minute=0),
    },
    "low-stock-report": {
        "task": "apps.inventory.tasks.low_stock_report",
        "schedule": crontab(hour=8, minute=0),
    },
    "abandoned-cart-cleanup": {
        "task": "apps.orders.tasks.abandoned_cart_cleanup",
        "schedule": crontab(hour=4, minute=0),
    },
}
