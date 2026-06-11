from django.contrib import admin
from .models import Booking, Passenger

class PassengerInline(admin.TabularInline):
    model = Passenger
    extra = 0
    raw_id_fields = ('seat',)
    fields = ('name', 'age', 'gender', 'seat', 'boarding_status')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'trip', 'status', 'total_amount', 'contact_email', 'booking_time')
    list_filter = ('status', 'booking_time')
    search_fields = ('user__username', 'contact_email', 'trip__route__origin', 'trip__route__destination')
    date_hierarchy = 'booking_time'
    filter_horizontal = ('seats',)
    inlines = [PassengerInline]

@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'gender', 'booking', 'seat', 'boarding_status')
    list_filter = ('gender', 'boarding_status')
    search_fields = ('name', 'booking__user__username')
    raw_id_fields = ('booking', 'seat')
