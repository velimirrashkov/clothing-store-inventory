"""Celery tasks. Thin wrappers over services.py (see architecture-spec.md §2.1)."""
from celery import shared_task
from django.utils import timezone


@shared_task
def abandoned_cart_cleanup():
    """Mark carts stale after 7 days (see architecture-spec.md §8.6)."""
    from .models import Cart

    cutoff = timezone.now() - timezone.timedelta(days=7)
    return Cart.objects.filter(status="active", updated_at__lt=cutoff).update(status="abandoned")
