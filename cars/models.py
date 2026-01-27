from django.db import models


class Car(models.Model):
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    engine = models.CharField(max_length=200)
    horsepower = models.PositiveIntegerField()
    top_speed = models.PositiveIntegerField(help_text="Top speed in km/h")
    acceleration = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        help_text="0-100 km/h time in seconds"
    )
    price = models.DecimalField(max_digits=12, decimal_places=2, help_text="MSRP in USD")
    image = models.ImageField(upload_to='cars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.year} {self.brand} {self.name}"
