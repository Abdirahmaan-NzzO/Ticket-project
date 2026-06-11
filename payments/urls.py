from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('create-checkout-session/<int:booking_id>/', views.create_checkout_session, name='create_checkout_session'),
    path('success/', views.payment_success, name='success'),
    path('cancel/', views.payment_cancel, name='cancel'),
    path('webhook/', views.stripe_webhook, name='webhook'),
    path('mock-confirm/<int:booking_id>/', views.mock_confirm_payment, name='mock_confirm_payment'),
    
    path('choose-payment/<int:booking_id>/', views.choose_payment_method, name='choose_payment_method'),
    path('local-payment/<int:booking_id>/', views.local_payment, name='local_payment'),
    path('local-success/<int:booking_id>/', views.local_success, name='local_success'),
]
