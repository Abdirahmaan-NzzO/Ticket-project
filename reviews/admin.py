from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('booking', 'driver', 'bus', 'rating', 'created_at')
    list_filter = ('rating', 'created_at', 'driver', 'bus')
    search_fields = ('booking__id', 'driver__user__username', 'bus__registration_number', 'comment')
    autocomplete_fields = ('booking', 'driver', 'bus')
