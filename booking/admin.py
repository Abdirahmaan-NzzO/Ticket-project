from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'trip', 'status', 'total_amount', 'booking_time')
    list_filter = ('status', 'booking_time')
    search_fields = ('user__username', 'user__email', 'trip__route__origin', 'trip__route__destination')
    date_hierarchy = 'booking_time'
    filter_horizontal = ('seats',)
