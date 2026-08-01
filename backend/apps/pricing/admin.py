from django.contrib import admin

from .models import Discount, DiscountTarget

admin.site.register(Discount)
admin.site.register(DiscountTarget)
