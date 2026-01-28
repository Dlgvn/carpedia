from django.db import models
from urllib.parse import quote


class Car(models.Model):
    """Main car model - represents a car model (not a specific generation)."""
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    description = models.TextField(blank=True, help_text="Short description of the car")
    body_style = models.CharField(max_length=100, blank=True)
    car_class = models.CharField(max_length=100, blank=True, help_text="e.g., Mid-size luxury SUV")
    production_years = models.CharField(max_length=100, blank=True, help_text="e.g., 2000-present")
    wiki_page_id = models.PositiveIntegerField(null=True, blank=True, unique=True)
    data_source = models.CharField(max_length=50, default='manual')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['brand', 'name']

    def __str__(self):
        return f"{self.brand} {self.name}"

    def get_image_url(self, angle='01'):
        """Get image URL from IMAGIN.Studio."""
        if self.brand and self.name:
            make = quote(self.brand)
            model_family = quote(self.name)
            # Get year from first generation if available
            gen = self.generations.first()
            model_year = gen.year_start if gen and gen.year_start else 2020
            return (
                f"https://cdn.imagin.studio/getimage"
                f"?customer=demo"
                f"&make={make}"
                f"&modelFamily={model_family}"
                f"&modelYear={model_year}"
                f"&zoomType=fullscreen"
                f"&angle={angle}"
                f"&width=800"
            )
        return None

    def get_gallery_images(self):
        """Get multiple image angles for gallery."""
        angles = ['01', '09', '13', '17', '21', '25', '29']
        return [self.get_image_url(angle) for angle in angles if self.get_image_url(angle)]


class Generation(models.Model):
    """Car generation - specific era/version of a car model."""
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='generations')
    name = models.CharField(max_length=100, blank=True, help_text="e.g., First Generation, Mk7")
    code = models.CharField(max_length=50, blank=True, help_text="e.g., W210, E39")
    year_start = models.PositiveIntegerField(null=True, blank=True)
    year_end = models.PositiveIntegerField(null=True, blank=True, help_text="Leave empty if still in production")

    # Specs
    engine = models.CharField(max_length=300, blank=True)
    horsepower = models.CharField(max_length=100, blank=True, help_text="e.g., 300 hp (224 kW)")
    torque = models.CharField(max_length=100, blank=True, help_text="e.g., 270 lb⋅ft (366 N⋅m)")
    top_speed = models.CharField(max_length=100, blank=True, help_text="e.g., 155 mph")
    acceleration = models.CharField(max_length=100, blank=True, help_text="0-60 or 0-100 time")
    transmission = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-year_start']

    def __str__(self):
        years = f"{self.year_start or '?'}-{self.year_end or 'present'}"
        if self.name:
            return f"{self.car.name} {self.name} ({years})"
        return f"{self.car.name} ({years})"

    def get_image_url(self, angle='01'):
        """Get image URL for this specific generation."""
        if self.car.brand and self.car.name:
            make = quote(self.car.brand)
            model_family = quote(self.car.name)
            model_year = self.year_start if self.year_start else 2020
            return (
                f"https://cdn.imagin.studio/getimage"
                f"?customer=demo"
                f"&make={make}"
                f"&modelFamily={model_family}"
                f"&modelYear={model_year}"
                f"&zoomType=fullscreen"
                f"&angle={angle}"
                f"&width=800"
            )
        return None

    def get_gallery_images(self):
        """Get multiple image angles for gallery."""
        angles = ['01', '09', '13', '17', '21', '25', '29']
        return [self.get_image_url(angle) for angle in angles if self.get_image_url(angle)]
