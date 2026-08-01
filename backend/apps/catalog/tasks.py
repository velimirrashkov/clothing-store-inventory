"""Celery tasks. Thin wrappers over services.py (see architecture-spec.md §2.1)."""
from celery import shared_task
from django.contrib.postgres.search import SearchVector


@shared_task
def rebuild_search_vector(product_id: int) -> None:
    """Runs on product save (see architecture-spec.md §8.6)."""
    from .models import Product

    Product.objects.filter(id=product_id).update(
        search_vector=SearchVector("name", weight="A") + SearchVector("description", "brand", weight="B")
    )


@shared_task
def generate_image_derivatives(media_id: int) -> None:
    """400w/800w/1600w WebP derivatives, written to object storage (see architecture-spec.md §8.1). Stub for Phase 2."""
    raise NotImplementedError("Wire up object storage + Pillow pipeline before enabling media uploads.")
