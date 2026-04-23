from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'trip', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'trip__route__origin', 'trip__route__destination')
    date_hierarchy = 'created_at'
    autocomplete_fields = ('user', 'trip')
