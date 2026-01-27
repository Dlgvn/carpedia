from django.db import models
from urllib.parse import quote


class Car(models.Model):
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    year = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    engine = models.CharField(max_length=200, blank=True)
    horsepower = models.PositiveIntegerField(null=True, blank=True)
    top_speed = models.PositiveIntegerField(null=True, blank=True, help_text="Top speed in km/h")
    acceleration = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="0-100 km/h time in seconds"
    )
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="MSRP in USD")
    image = models.ImageField(upload_to='cars/', blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, help_text="External image URL")
    wiki_page_id = models.PositiveIntegerField(null=True, blank=True, unique=True, help_text="Autopedia wiki page ID")
    created_at = models.DateTimeField(auto_now_add=True)

    # New generation and spec fields
    generation_code = models.CharField(max_length=50, blank=True, help_text="e.g., W210, Mk7, E39")
    generation_years = models.CharField(max_length=50, blank=True, help_text="e.g., 1995-2002")
    transmission = models.CharField(max_length=200, blank=True)
    fuel_type = models.CharField(max_length=100, blank=True)
    body_style = models.CharField(max_length=100, blank=True)
    wikipedia_page_id = models.PositiveIntegerField(null=True, blank=True, unique=True, help_text="Wikipedia page ID")
    data_source = models.CharField(max_length=50, default='manual', help_text="manual, wikipedia, autopedia")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.year:
            return f"{self.year} {self.brand} {self.name}"
        return f"{self.brand} {self.name}"

    def get_image_url(self):
        """Get image URL, preferring IMAGIN.Studio 3D render, then external URL, then uploaded image."""
        if self.brand and self.name:
            make = quote(self.brand)
            model_family = quote(self.name)
            model_year = self.year if self.year else 2020
            return (
                f"https://cdn.imagin.studio/getimage"
                f"?customer=demo"
                f"&make={make}"
                f"&modelFamily={model_family}"
                f"&modelYear={model_year}"
                f"&zoomType=fullscreen"
                f"&angle=01"
                f"&width=800"
            )
        if self.image_url:
            return self.image_url
        if self.image:
            return self.image.url
        return None
