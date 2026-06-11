from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'payment_method', 'status', 'sender_number', 'sender_name', 'payment_date')
    list_filter = ('status', 'payment_method', 'payment_date')
    search_fields = ('transaction_id', 'booking__user__username', 'sender_number', 'sender_name')
    date_hierarchy = 'payment_date'
