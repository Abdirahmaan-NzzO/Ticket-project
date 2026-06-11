from django.contrib import admin
from .models import DriverProfile, DriverNotification

@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'operator', 'license_number', 'phone', 'experience_years', 'status')
    list_filter = ('operator', 'status', 'experience_years')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'license_number', 'phone')
    raw_id_fields = ('user', 'operator')

@admin.register(DriverNotification)
class DriverNotificationAdmin(admin.ModelAdmin):
    list_display = ('driver', 'title', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('driver__user__username', 'title', 'message')
