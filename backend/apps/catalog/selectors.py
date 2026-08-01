"""Read queries only. Nothing here writes (see architecture-spec.md §2.1)."""
from django.contrib.postgres.search import SearchQuery, SearchRank, TrigramSimilarity
from django.db.models import Q, QuerySet

from .models import Category, Product


def active_products() -> QuerySet[Product]:
    return Product.objects.filter(status="active").select_related("category")


def product_by_slug(slug: str) -> Product:
    return active_products().prefetch_related("variants", "media").get(slug=slug)


def search_products(query: str, *, category_slug: str | None = None) -> QuerySet[Product]:
    """Postgres tsvector with a trigram fallback for typos (see architecture-spec.md §8.1)."""
    qs = active_products()
    if category_slug:
        qs = qs.filter(category__slug=category_slug)
    if not query:
        return qs

    search_query = SearchQuery(query)
    ranked = qs.annotate(rank=SearchRank("search_vector", search_query)).filter(search_vector=search_query)
    if ranked.exists():
        return ranked.order_by("-rank")

    return qs.annotate(similarity=TrigramSimilarity("name", query)).filter(
        Q(similarity__gt=0.2) | Q(name__icontains=query)
    ).order_by("-similarity")


def category_tree() -> QuerySet[Category]:
    return Category.objects.filter(is_active=True).select_related("parent")
