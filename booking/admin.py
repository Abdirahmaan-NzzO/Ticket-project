from django.contrib import admin
from .models import BusOperator, Bus, Route, Seat, Trip, Booking, Payment

@admin.register(BusOperator)
class BusOperatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email', 'phone_number', 'created_at')
    search_fields = ('name', 'contact_email')

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'operator', 'capacity')
    list_filter = ('operator',)
    search_fields = ('registration_number',)

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('origin', 'destination')
    search_fields = ('origin', 'destination')

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('seat_number', 'bus')
    list_filter = ('bus',)
    search_fields = ('seat_number', 'bus__registration_number')

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('route', 'bus', 'departure_time', 'arrival_time', 'price')
    list_filter = ('route', 'departure_time', 'bus')
    search_fields = ('route__origin', 'route__destination', 'bus__registration_number')
    date_hierarchy = 'departure_time'

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'trip', 'status', 'total_amount', 'booking_time')
    list_filter = ('status', 'booking_time')
    search_fields = ('user__username', 'user__email', 'trip__route__origin', 'trip__route__destination')
    date_hierarchy = 'booking_time'
    filter_horizontal = ('seats',)  # Improved UI for the many-to-many seats selection

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'payment_method', 'status', 'transaction_id', 'payment_date')
    list_filter = ('status', 'payment_method', 'payment_date')
    search_fields = ('transaction_id', 'booking__user__username')
