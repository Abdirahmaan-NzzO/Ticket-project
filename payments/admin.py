from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'payment_method', 'status', 'sender_number', 'sender_name', 'payment_date')
    list_filter = ('status', 'payment_method', 'payment_date')
    search_fields = ('transaction_id', 'booking__user__username', 'sender_number', 'sender_name')
    date_hierarchy = 'payment_date'
    actions = ['confirm_payments']

    @admin.action(description='Confirm selected payments and bookings')
    def confirm_payments(self, request, queryset):
        updated_count = 0
        for payment in queryset:
            if payment.status != 'COMPLETED':
                payment.status = 'COMPLETED'
                payment.save()
                updated_count += 1
        self.message_user(
            request, 
            f"Successfully confirmed {updated_count} payment(s) and their associated booking(s)."
        )

