from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from apps.accounts.roles import ROLE_INHERITANCE, ROLE_PERMISSIONS


class Command(BaseCommand):
    help = "Create/update the worker, manager and admin Groups from apps/accounts/roles.py."

    def handle(self, *args, **options):
        for role, direct_codenames in ROLE_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=role)

            codenames = set(direct_codenames)
            for inherited_role in ROLE_INHERITANCE.get(role, []):
                codenames |= set(ROLE_PERMISSIONS.get(inherited_role, []))

            perms = []
            missing = []
            for codename in codenames:
                app_label, _, codename_only = codename.partition(".")
                perm = Permission.objects.filter(content_type__app_label=app_label, codename=codename_only).first()
                if perm:
                    perms.append(perm)
                else:
                    missing.append(codename)

            group.permissions.set(perms)
            self.stdout.write(self.style.SUCCESS(f"{role}: {len(perms)} permissions"))
            if missing:
                self.stdout.write(self.style.WARNING(f"  missing (not yet declared in Meta.permissions): {missing}"))
