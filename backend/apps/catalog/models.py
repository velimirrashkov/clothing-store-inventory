
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models

from apps.core.models import PublicIdModel, TimeStampedModel


class Category(models.Model):
    """Self-referential tree. Rendered lazily by the frontend — never a flat list (see architecture-spec.md §9)."""

    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="children")
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    position = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["position", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(TimeStampedModel, PublicIdModel):
    STATUS_CHOICES = [("draft", "draft"), ("active", "active"), ("archived", "archived")]
    GENDER_CHOICES = [("men", "men"), ("women", "women"), ("unisex", "unisex"), ("kids", "kids")]

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    brand = models.CharField(max_length=120, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    season = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    archived_at = models.DateTimeField(null=True, blank=True)
    search_vector = SearchVectorField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "category"]),
            GinIndex(fields=["search_vector"]),
        ]

    def __str__(self):
        return self.name


class Variant(TimeStampedModel, PublicIdModel):
    """THE stock-keeping unit (see architecture-spec.md §4.3)."""

    product = models.ForeignKey(Product, on_delete=models.RESTRICT, related_name="variants")
    sku = models.CharField(max_length=64, unique=True)
    barcode = models.CharField(max_length=32, unique=True, null=True, blank=True)
    size = models.CharField(max_length=20)
    color = models.CharField(max_length=40)
    color_hex = models.CharField(max_length=7, null=True, blank=True)
    price_amount = models.BigIntegerField()  # minor units — never a float
    currency = models.CharField(max_length=3, default="EUR")
    compare_at_amount = models.BigIntegerField(null=True, blank=True)
    weight_grams = models.IntegerField(null=True, blank=True)
    online_buffer = models.IntegerField(default=0)  # see architecture-spec.md §5.5 overselling policy
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "size", "color"], name="uniq_variant_product_size_color"),
        ]
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["barcode"]),
            models.Index(fields=["product"]),
        ]

    def __str__(self):
        return self.sku


class ProductMedia(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="media")
    variant = models.ForeignKey(Variant, null=True, blank=True, on_delete=models.CASCADE, related_name="media")
    url = models.URLField()
    alt_text = models.CharField(max_length=255, blank=True)
    position = models.IntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["position"]
