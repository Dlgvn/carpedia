from django.contrib import admin
from .models import Car


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'year', 'horsepower', 'price', 'created_at']
    list_filter = ['brand', 'year']
    search_fields = ['name', 'brand', 'description']
    ordering = ['-created_at']
