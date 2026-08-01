from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import LoginAttempt, TOTPDevice, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("email", "username", "is_staff", "is_active", "mfa_enabled")
    ordering = ("email",)


admin.site.register(TOTPDevice)
admin.site.register(LoginAttempt)
