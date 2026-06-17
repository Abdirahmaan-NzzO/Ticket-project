from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from listing.models import Seat, Trip

class Booking(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='booking_set')
    seats = models.ManyToManyField(Seat)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    booking_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking #{self.id} by {self.user.username}"

    def book_seats(self, seat_list):
        """
        Helper method to safely book seats by checking availability first.
        Should be called after the booking instance is saved.
        """
        for seat in seat_list:
            if seat.bus != self.trip.bus:
                raise ValidationError(f"Seat {seat.seat_number} does not belong to the correct bus.")
            if not self.trip.is_seat_available(seat):
                raise ValidationError(f"Seat {seat.seat_number} is already booked for this trip.")
        
        self.seats.add(*seat_list)
        self.total_amount = self.trip.price * len(seat_list)
        self.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        payment = getattr(self, 'payment', None)
        if payment:
            if self.status == 'CONFIRMED' and payment.status != 'COMPLETED':
                payment.status = 'COMPLETED'
                payment.save(update_fields=['status'])
            elif self.status == 'CANCELLED' and payment.status != 'FAILED':
                payment.status = 'FAILED'
                payment.save(update_fields=['status'])

    @property
    def can_be_reviewed(self):
        from django.utils import timezone
        if self.status != 'CONFIRMED':
            return False
        if hasattr(self, 'review'):
            return False
        if not self.trip.bus.driver:
            return False
        return self.trip.status == 'COMPLETED' or self.trip.arrival_time <= timezone.now()

class Passenger(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    BOARDING_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('BOARDED', 'Boarded'),
        ('NO_SHOW', 'No Show'),
    )
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='passengers')
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    boarding_status = models.CharField(max_length=20, choices=BOARDING_STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"{self.name} ({self.seat.seat_number})"
