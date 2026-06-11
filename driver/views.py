from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .decorators import driver_required
from .models import DriverProfile, DriverNotification
from .forms import DriverProfileForm, DelayReportForm
from listing.models import Trip, Bus
from booking.models import Booking, Passenger

@login_required
@driver_required
def driver_dashboard_view(request):
    driver_profile = request.user.driver_profile
    buses = driver_profile.buses.all()
    
    # Get all trips assigned to this driver's buses
    trips = Trip.objects.filter(bus__in=buses).order_by('-departure_time')
    
    upcoming_trips = trips.filter(
        Q(status='SCHEDULED') | Q(status='STARTED') | Q(status='DELAYED')
    ).order_by('departure_time')
    
    completed_trips = trips.filter(status='COMPLETED')
    
    # Calculate stats
    total_trips = trips.count()
    completed_count = completed_trips.count()
    upcoming_count = upcoming_trips.count()
    
    # Notifications
    notifications = driver_profile.notifications.all().order_by('-created_at')[:10]
    
    # Handle Profile Form Submission directly on dashboard
    if request.method == 'POST' and 'update_profile' in request.POST:
        profile_form = DriverProfileForm(request.POST, request.FILES, instance=driver_profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('driver:dashboard')
    else:
        profile_form = DriverProfileForm(instance=driver_profile)
        
    context = {
        'driver': driver_profile,
        'buses': buses,
        'upcoming_trips': upcoming_trips,
        'completed_trips': completed_trips[:5], # show last 5 completed
        'total_trips': total_trips,
        'completed_count': completed_count,
        'upcoming_count': upcoming_count,
        'notifications': notifications,
        'profile_form': profile_form,
    }
    return render(request, 'driver/dashboard.html', context)

@login_required
@driver_required
@require_POST
def driver_status_update_view(request):
    driver_profile = request.user.driver_profile
    new_status = request.POST.get('status')
    
    if new_status in ['ACTIVE', 'INACTIVE']:
        if driver_profile.status == 'ON_TRIP':
            messages.error(request, "Cannot change status while on an active trip!")
        else:
            driver_profile.status = new_status
            driver_profile.save()
            messages.success(request, f"Your status has been updated to {driver_profile.get_status_display()}.")
    else:
        messages.error(request, "Invalid status choice.")
        
    return redirect('driver:dashboard')

@login_required
@driver_required
def driver_trip_detail_view(request, trip_id):
    driver_profile = request.user.driver_profile
    trip = get_object_or_404(Trip, id=trip_id, bus__driver=driver_profile)
    
    # Retrieve passengers on confirmed bookings
    passengers = Passenger.objects.filter(
        booking__trip=trip, 
        booking__status='CONFIRMED'
    ).order_by('seat__seat_number')
    
    boarded_count = passengers.filter(boarding_status='BOARDED').count()
    no_show_count = passengers.filter(boarding_status='NO_SHOW').count()
    pending_count = passengers.filter(boarding_status='PENDING').count()
    
    context = {
        'trip': trip,
        'passengers': passengers,
        'boarded_count': boarded_count,
        'no_show_count': no_show_count,
        'pending_count': pending_count,
        'total_passengers': passengers.count(),
    }
    return render(request, 'driver/trip_detail.html', context)

@login_required
@driver_required
@require_POST
def start_trip_view(request, trip_id):
    driver_profile = request.user.driver_profile
    trip = get_object_or_404(Trip, id=trip_id, bus__driver=driver_profile)
    
    if trip.status == 'SCHEDULED' or trip.status == 'DELAYED':
        trip.status = 'STARTED'
        trip.save()
        
        driver_profile.status = 'ON_TRIP'
        driver_profile.save()
        
        # Create log notification
        DriverNotification.objects.create(
            driver=driver_profile,
            title="Trip Started",
            message=f"Trip from {trip.route.origin} to {trip.route.destination} has officially started."
        )
        messages.success(request, f"Trip to {trip.route.destination} has been started!")
    else:
        messages.warning(request, "This trip cannot be started.")
        
    return redirect('driver:trip_detail', trip_id=trip.id)

@login_required
@driver_required
@require_POST
def complete_trip_view(request, trip_id):
    driver_profile = request.user.driver_profile
    trip = get_object_or_404(Trip, id=trip_id, bus__driver=driver_profile)
    
    if trip.status == 'STARTED':
        trip.status = 'COMPLETED'
        trip.save()
        
        driver_profile.status = 'ACTIVE'
        driver_profile.save()
        
        # Create log notification
        DriverNotification.objects.create(
            driver=driver_profile,
            title="Trip Completed",
            message=f"Trip from {trip.route.origin} to {trip.route.destination} has been completed successfully."
        )
        messages.success(request, f"Trip to {trip.route.destination} has been marked as completed. Safe drive!")
    else:
        messages.warning(request, "This trip cannot be completed.")
        
    return redirect('driver:dashboard')

@login_required
@driver_required
def report_delay_view(request, trip_id):
    driver_profile = request.user.driver_profile
    trip = get_object_or_404(Trip, id=trip_id, bus__driver=driver_profile)
    
    if request.method == 'POST':
        form = DelayReportForm(request.POST, instance=trip)
        if form.is_valid():
            trip_instance = form.save(commit=False)
            trip_instance.status = 'DELAYED'
            trip_instance.save()
            
            # Notify
            DriverNotification.objects.create(
                driver=driver_profile,
                title="Delay Reported",
                message=f"A delay of {trip_instance.delay_minutes} minutes reported for trip to {trip.route.destination}."
            )
            messages.success(request, "Delay reported successfully.")
            return redirect('driver:trip_detail', trip_id=trip.id)
    else:
        form = DelayReportForm(instance=trip)
        
    context = {
        'trip': trip,
        'form': form,
    }
    return render(request, 'driver/report_delay.html', context)

@login_required
@driver_required
@require_POST
def passenger_board_view(request, passenger_id, status):
    driver_profile = request.user.driver_profile
    passenger = get_object_or_404(Passenger, id=passenger_id, booking__trip__bus__driver=driver_profile)
    
    if status in ['BOARDED', 'NO_SHOW', 'PENDING']:
        passenger.boarding_status = status
        passenger.save()
        messages.success(request, f"Passenger {passenger.name} marked as {status.lower().replace('_', ' ')}.")
    else:
        messages.error(request, "Invalid boarding status.")
        
    return redirect('driver:trip_detail', trip_id=passenger.booking.trip.id)

@login_required
@driver_required
def mark_notification_read_view(request, notification_id):
    driver_profile = request.user.driver_profile
    notification = get_object_or_404(DriverNotification, id=notification_id, driver=driver_profile)
    notification.is_read = True
    notification.save()
    return redirect('driver:dashboard')
