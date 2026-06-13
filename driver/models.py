from django.db import models
from django.contrib.auth.models import User

class DriverProfile(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('ON_TRIP', 'On Trip'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    operator = models.ForeignKey('listing.BusOperator', on_delete=models.SET_NULL, null=True, blank=True, related_name='drivers')
    license_number = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)
    experience_years = models.PositiveIntegerField(default=0)
    emergency_contact = models.CharField(max_length=100, blank=True, null=True)
    photo = models.ImageField(upload_to='driver_photos/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    def get_average_rating(self):
        from django.db.models import Avg
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0.0

    def get_review_count(self):
        return self.reviews.count()

    def __str__(self):
        return f"Driver: {self.user.get_full_name() or self.user.username} ({self.license_number})"

class DriverNotification(models.Model):
    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.driver.user.username}: {self.title}"
