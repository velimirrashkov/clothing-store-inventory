"""Celery tasks. Thin wrappers over services.py (see architecture-spec.md §2.1, §8.6)."""
import logging

from celery import shared_task

from . import services
from .events import low_stock_reached

logger = logging.getLogger(__name__)


@shared_task
def expire_stale_reservations():
    count = services.expire_stale_reservations()
    logger.info("expired %s stale reservations", count)
    return count


@shared_task
def reconcile_stock_levels():
    mismatches = services.reconcile_levels()
    if mismatches:
        logger.warning("stock reconciliation found %s mismatches: %s", len(mismatches), mismatches)
    return mismatches


@shared_task
def low_stock_report(threshold: int = 5):
    """Email variants below threshold (see architecture-spec.md §8.6). Mailer wiring is a Phase 2 seam."""
    levels = list(services.low_stock_variants(threshold))
    for level in levels:
        low_stock_reached.send(
            sender=None, variant_id=level.variant_id, location_id=level.location_id,
            available=level.available, threshold=threshold,
        )
    logger.info("%s variants at/below low-stock threshold %s", len(levels), threshold)
    return [level.variant_id for level in levels]
