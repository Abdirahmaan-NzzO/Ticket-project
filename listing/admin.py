from django.contrib import admin
from .models import BusOperator, Bus, Route, Seat, Trip

@admin.register(BusOperator)
class BusOperatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email', 'phone_number', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'contact_email')
    date_hierarchy = 'created_at'

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'operator', 'capacity')
    list_filter = ('operator',)
    search_fields = ('registration_number',)
    autocomplete_fields = ('operator',)

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('origin', 'destination')
    search_fields = ('origin', 'destination')

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('seat_number', 'bus')
    list_filter = ('bus',)
    search_fields = ('seat_number', 'bus__registration_number')
    autocomplete_fields = ('bus',)

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('route', 'bus', 'departure_time', 'arrival_time', 'price')
    list_filter = ('route', 'departure_time', 'bus')
    search_fields = ('route__origin', 'route__destination', 'bus__registration_number')
    date_hierarchy = 'departure_time'
    autocomplete_fields = ('route', 'bus')
