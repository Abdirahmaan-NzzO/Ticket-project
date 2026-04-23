from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class BusOperator(models.Model):
    name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Bus(models.Model):
    operator = models.ForeignKey(BusOperator, on_delete=models.CASCADE, related_name='buses')
    registration_number = models.CharField(max_length=50, unique=True)
    capacity = models.PositiveIntegerField()

    class Meta:
        verbose_name_plural = "Buses"

    def __str__(self):
        return f"{self.registration_number} ({self.operator.name})"

class Route(models.Model):
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.origin} to {self.destination}"

class Seat(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.CharField(max_length=10)
    
    class Meta:
        unique_together = ('bus', 'seat_number')

    def __str__(self):
        return f"Seat {self.seat_number} on {self.bus.registration_number}"

class Trip(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='trips')
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='trips')
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.route} at {self.departure_time.strftime('%Y-%m-%d %H:%M')}"

    def get_booked_seats(self):
        """Returns a list of seats that are already booked and confirmed for this trip."""
        return Seat.objects.filter(booking__trip=self, booking__status='CONFIRMED')

    def get_available_seats(self):
        """Returns all seats on the bus that are not yet booked for this trip."""
        booked_seats = self.get_booked_seats()
        return self.bus.seats.exclude(id__in=booked_seats.values_list('id', flat=True))

    def is_seat_available(self, seat):
        """Checks if a specific seat is available for this trip."""
        return not self.booking_set.filter(status='CONFIRMED', seats=seat).exists()

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

class Payment(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    payment_method = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Booking #{self.booking.id}"
