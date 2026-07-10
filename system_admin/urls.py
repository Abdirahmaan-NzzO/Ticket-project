from django.urls import path
from . import views

app_name = 'system_admin'

urlpatterns = [
    # Dashboard Overview
    path('', views.dashboard_overview, name='dashboard'),
    
    # Bookings
    path('bookings/', views.bookings_list, name='bookings_list'),
    path('bookings/<int:pk>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:pk>/status/<str:status>/', views.booking_status_update, name='booking_status_update'),
    
    # Trips
    path('trips/', views.trips_list, name='trips_list'),
    path('trips/new/', views.trip_create, name='trip_create'),
    path('trips/<int:pk>/edit/', views.trip_edit, name='trip_edit'),
    path('trips/<int:pk>/delete/', views.trip_delete, name='trip_delete'),
    
    # Routes
    path('routes/new/', views.route_create, name='route_create'),
    
    # Buses
    path('buses/', views.buses_list, name='buses_list'),
    path('buses/new/', views.bus_create, name='bus_create'),
    path('buses/<int:pk>/edit/', views.bus_edit, name='bus_edit'),
    path('buses/<int:pk>/delete/', views.bus_delete, name='bus_delete'),
    
    # Operators
    path('operators/new/', views.operator_create, name='operator_create'),
    path('operators/<int:pk>/edit/', views.operator_edit, name='operator_edit'),
    path('operators/<int:pk>/delete/', views.operator_delete, name='operator_delete'),
    
    # Drivers
    path('drivers/', views.drivers_list, name='drivers_list'),
    path('drivers/new/', views.driver_create, name='driver_create'),
    path('drivers/<int:pk>/edit/', views.driver_edit, name='driver_edit'),
    path('drivers/<int:pk>/delete/', views.driver_delete, name='driver_delete'),
    path('drivers/<int:pk>/notify/', views.notify_driver, name='notify_driver'),
    
    # Payments
    path('payments/', views.payments_list, name='payments_list'),
    path('payments/<int:pk>/status/<str:status>/', views.payment_status_update, name='payment_status_update'),
    
    # Users
    path('users/', views.users_list, name='users_list'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:pk>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('users/<int:pk>/toggle-staff/', views.user_toggle_staff, name='user_toggle_staff'),
    
    # Reviews
    path('reviews/', views.reviews_list, name='reviews_list'),
    path('reviews/<int:pk>/delete/', views.review_delete, name='review_delete'),
]
