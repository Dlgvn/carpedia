from django.contrib import admin
from .models import Car


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'year', 'generation_code', 'horsepower', 'body_style', 'data_source', 'created_at']
    list_filter = ['brand', 'year', 'body_style', 'fuel_type', 'data_source']
    search_fields = ['name', 'brand', 'description', 'generation_code', 'engine']
    ordering = ['-created_at']
    readonly_fields = ['wikipedia_page_id', 'wiki_page_id', 'created_at']

    fieldsets = (
        (None, {
            'fields': ('name', 'brand', 'year', 'description')
        }),
        ('Generation Info', {
            'fields': ('generation_code', 'generation_years')
        }),
        ('Specifications', {
            'fields': ('engine', 'horsepower', 'top_speed', 'acceleration', 'transmission', 'fuel_type', 'body_style')
        }),
        ('Pricing & Images', {
            'fields': ('price', 'image', 'image_url')
        }),
        ('Data Source', {
            'fields': ('data_source', 'wiki_page_id', 'wikipedia_page_id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
