from django.core.management.base import BaseCommand

from apps.inventory.models import Location


class Command(BaseCommand):
    """Single physical store + online shop share one warehouse/location (see architecture-spec.md, Scope)."""

    help = "Idempotently create the single default Location row."

    def handle(self, *args, **options):
        location, created = Location.objects.get_or_create(
            code="MAIN", defaults={"name": "Main Store", "is_default": True}
        )
        if not created and not location.is_default:
            location.is_default = True
            location.save(update_fields=["is_default"])
        state = "created" if created else "exists"
        self.stdout.write(self.style.SUCCESS(f"Default location: {location.name} ({state})"))
