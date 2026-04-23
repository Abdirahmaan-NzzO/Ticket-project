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
