from django.contrib import admin
from .models import Car, Generation


class GenerationInline(admin.TabularInline):
    model = Generation
    extra = 1
    fields = ['name', 'code', 'year_start', 'year_end', 'engine', 'horsepower', 'torque', 'top_speed', 'acceleration', 'transmission']


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'body_style', 'production_years', 'data_source', 'created_at']
    list_filter = ['brand', 'body_style', 'data_source']
    search_fields = ['name', 'brand', 'description']
    ordering = ['brand', 'name']
    readonly_fields = ['wiki_page_id', 'created_at']
    inlines = [GenerationInline]

    fieldsets = (
        (None, {
            'fields': ('name', 'brand', 'description')
        }),
        ('Classification', {
            'fields': ('body_style', 'car_class', 'production_years')
        }),
        ('Data Source', {
            'fields': ('data_source', 'wiki_page_id', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Generation)
class GenerationAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'car', 'year_start', 'year_end', 'engine', 'horsepower']
    list_filter = ['car__brand', 'year_start']
    search_fields = ['car__name', 'car__brand', 'name', 'code', 'engine']
    autocomplete_fields = ['car']
