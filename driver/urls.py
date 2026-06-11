from django.urls import path
from . import views

app_name = 'driver'

urlpatterns = [
    path('dashboard/', views.driver_dashboard_view, name='dashboard'),
    path('status-update/', views.driver_status_update_view, name='status_update'),
    path('trip/<int:trip_id>/', views.driver_trip_detail_view, name='trip_detail'),
    path('trip/<int:trip_id>/start/', views.start_trip_view, name='start_trip'),
    path('trip/<int:trip_id>/complete/', views.complete_trip_view, name='complete_trip'),
    path('trip/<int:trip_id>/delay/', views.report_delay_view, name='report_delay'),
    path('passenger/<int:passenger_id>/board/<str:status>/', views.passenger_board_view, name='passenger_board'),
    path('notification/<int:notification_id>/read/', views.mark_notification_read_view, name='mark_notification_read'),
]
