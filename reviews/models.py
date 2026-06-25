from django.db import models
from booking.models import Booking
from driver.models import DriverProfile
from listing.models import Bus

class Review(models.Model):
    RATING_CHOICES = (
        (1, '1 - Terrible'),
        (2, '2 - Poor'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    )
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, related_name='reviews')
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='reviews')
    
    rating = models.PositiveIntegerField(choices=RATING_CHOICES, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    bus_rating = models.PositiveIntegerField(choices=RATING_CHOICES, default=5)
    bus_comment = models.TextField(blank=True, null=True)
    driver_rating = models.PositiveIntegerField(choices=RATING_CHOICES, default=5)
    driver_comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for Booking #{self.booking.id} - {self.rating or self.bus_rating} Stars"
