from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('book/<int:trip_id>/', views.book_trip_view, name='book_trip'),
    path('passenger-details/<int:trip_id>/', views.passenger_details_view, name='passenger_details'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
]
