from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from datetime import timedelta

from .decorators import admin_required
from .forms import (
    TripForm, RouteForm, BusForm, BusOperatorForm, 
    DriverProfileForm, DriverNotificationForm, UserAdminForm
)
from booking.models import Booking, Passenger
from listing.models import Trip, Route, Bus, BusOperator, Seat, Amenity
from driver.models import DriverProfile, DriverNotification
from payments.models import Payment
from reviews.models import Review
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
@admin_required
def dashboard_overview(request):
    # Calculations for KPIs
    total_revenue = Payment.objects.filter(status='COMPLETED').aggregate(Sum('amount'))['amount__sum'] or 0.00
    total_bookings = Booking.objects.count()
    pending_bookings = Booking.objects.filter(status='PENDING').count()
    confirmed_bookings = Booking.objects.filter(status='CONFIRMED').count()
    cancelled_bookings = Booking.objects.filter(status='CANCELLED').count()
    
    active_drivers = DriverProfile.objects.filter(status__in=['ACTIVE', 'ON_TRIP']).count()
    active_buses = Bus.objects.count()
    scheduled_trips = Trip.objects.filter(status__in=['SCHEDULED', 'STARTED', 'DELAYED']).count()
    
    avg_rating = Review.objects.aggregate(Avg('rating'))['rating__avg']
    avg_rating = round(avg_rating, 2) if avg_rating else 0.00
    
    # Recent items
    recent_bookings = Booking.objects.select_related('user', 'trip').order_by('-booking_time')[:5]
    recent_reviews = Review.objects.select_related('booking__user', 'driver', 'bus').order_by('-created_at')[:5]
    recent_users = User.objects.order_by('-date_joined')[:5]
    
    # Chart data - Revenue of completed payments for the past 7 days
    today = timezone.now().date()
    days = []
    revenue_chart_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        days.append(day.strftime('%b %d'))
        day_revenue = Payment.objects.filter(
            status='COMPLETED', 
            payment_date__date=day
        ).aggregate(Sum('amount'))['amount__sum'] or 0.00
        revenue_chart_data.append(float(day_revenue))
        
    context = {
        'total_revenue': total_revenue,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'confirmed_bookings': confirmed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'active_drivers': active_drivers,
        'active_buses': active_buses,
        'scheduled_trips': scheduled_trips,
        'avg_rating': avg_rating,
        'recent_bookings': recent_bookings,
        'recent_reviews': recent_reviews,
        'recent_users': recent_users,
        'chart_labels': days,
        'chart_data': revenue_chart_data,
        'active_tab': 'overview'
    }
    return render(request, 'system_admin/dashboard.html', context)

# --- Booking Views ---

@login_required
@admin_required
def bookings_list(request):
    bookings_qs = Booking.objects.select_related('user', 'trip__route', 'trip__bus').order_by('-booking_time')
    
    # Filters
    q = request.GET.get('q', '')
    if q:
        bookings_qs = bookings_qs.filter(
            Q(user__username__icontains=q) |
            Q(user__email__icontains=q) |
            Q(contact_phone__icontains=q) |
            Q(id__icontains=q)
        )
        
    status = request.GET.get('status', '')
    if status:
        bookings_qs = bookings_qs.filter(status=status)
        
    paginator = Paginator(bookings_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'q': q,
        'status': status,
        'active_tab': 'bookings'
    }
    return render(request, 'system_admin/dashboard.html', context)

@login_required
@admin_required
def booking_detail(request, pk):
    booking = get_object_or_404(Booking.objects.select_related('user', 'trip__route', 'trip__bus'), pk=pk)
    passengers = booking.passengers.all()
    payment = getattr(booking, 'payment', None)
    
    context = {
        'booking': booking,
        'passengers': passengers,
        'payment': payment,
    }
    return render(request, 'system_admin/booking_detail.html', context)

@login_required
@admin_required
@require_POST
def booking_status_update(request, pk, status):
    booking = get_object_or_404(Booking, pk=pk)
    if status in ['CONFIRMED', 'PENDING', 'CANCELLED']:
        booking.status = status
        booking.save()
        messages.success(request, f"Booking #{booking.id} status updated to {status.lower()}.")
    else:
        messages.error(request, "Invalid booking status change.")
    return redirect(request.META.get('HTTP_REFERER', 'system_admin:bookings_list'))

# --- Trip Detail View ---

@login_required
@admin_required
def trip_detail(request, pk):
    trip = get_object_or_404(Trip.objects.select_related('bus__operator', 'bus__driver__user', 'route'), pk=pk)
    bookings = Booking.objects.filter(trip=trip).select_related('user').order_by('-booking_time')
    context = {
        'trip': trip,
        'bookings': bookings,
        'active_tab': 'trips',
    }
    return render(request, 'system_admin/trip_detail.html', context)

# --- Trips & Routes Views ---

@login_required
@admin_required
def trips_list(request):
    trips_qs = Trip.objects.select_related('bus__operator', 'route').order_by('-departure_time')
    routes = Route.objects.all().order_by('origin')
    
    # Filters
    q = request.GET.get('q', '')
    if q:
        trips_qs = trips_qs.filter(
            Q(route__origin__icontains=q) |
            Q(route__destination__icontains=q) |
            Q(bus__registration_number__icontains=q)
        )
        
    status = request.GET.get('status', '')
    if status:
        trips_qs = trips_qs.filter(status=status)
        
    paginator = Paginator(trips_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'routes': routes,
        'q': q,
        'status': status,
        'active_tab': 'trips'
    }
    return render(request, 'system_admin/dashboard.html', context)

@login_required
@admin_required
def trip_create(request):
    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            trip = form.save()
            messages.success(request, f"Trip from {trip.route} successfully scheduled!")
            return redirect('system_admin:trips_list')
    else:
        form = TripForm()
    return render(request, 'system_admin/trip_form.html', {'form': form, 'title': 'Schedule New Trip'})

@login_required
@admin_required
def trip_edit(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if request.method == 'POST':
        form = TripForm(request.POST, instance=trip)
        if form.is_valid():
            form.save()
            messages.success(request, f"Trip details updated successfully!")
            return redirect('system_admin:trips_list')
    else:
        form = TripForm(instance=trip)
    return render(request, 'system_admin/trip_form.html', {'form': form, 'title': 'Edit Scheduled Trip', 'trip': trip})

@login_required
@admin_required
@require_POST
def trip_delete(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    trip.delete()
    messages.success(request, "Trip deleted successfully.")
    return redirect('system_admin:trips_list')

@login_required
@admin_required
def route_create(request):
    if request.method == 'POST':
        form = RouteForm(request.POST)
        if form.is_valid():
            route = form.save()
            messages.success(request, f"Route {route} created successfully!")
            return redirect('system_admin:trips_list')
    else:
        form = RouteForm()
    return render(request, 'system_admin/route_form.html', {'form': form, 'title': 'Add New Route'})

@login_required
@admin_required
def route_edit(request, pk):
    route = get_object_or_404(Route, pk=pk)
    if request.method == 'POST':
        form = RouteForm(request.POST, instance=route)
        if form.is_valid():
            form.save()
            messages.success(request, f"Route {route} updated successfully!")
            return redirect('system_admin:trips_list')
    else:
        form = RouteForm(instance=route)
    return render(request, 'system_admin/route_form.html', {'form': form, 'title': 'Edit Route', 'route': route})

@login_required
@admin_required
@require_POST
def route_delete(request, pk):
    route = get_object_or_404(Route, pk=pk)
    route.delete()
    messages.success(request, "Route deleted successfully.")
    return redirect('system_admin:trips_list')

# --- Buses & Operators Views ---

@login_required
@admin_required
def buses_list(request):
    buses = Bus.objects.select_related('operator', 'driver__user').prefetch_related('amenities').all().order_by('id')
    operators = BusOperator.objects.all().order_by('-created_at')
    
    context = {
        'buses': buses,
        'operators': operators,
        'active_tab': 'buses'
    }
    return render(request, 'system_admin/dashboard.html', context)

@login_required
@admin_required
def bus_create(request):
    if request.method == 'POST':
        form = BusForm(request.POST)
        if form.is_valid():
            bus = form.save()
            
            # --- AUTO GENERATE SEATS ---
            capacity = bus.capacity
            seats_to_create = []
            rows = (capacity + 3) // 4  # 4 seats per row (2+2 layout)
            labels = ['A', 'B', 'C', 'D']
            count = 0
            for r in range(1, rows + 1):
                for label in labels:
                    if count >= capacity:
                        break
                    seat_number = f"{r}{label}"
                    seats_to_create.append(Seat(bus=bus, seat_number=seat_number))
                    count += 1
            Seat.objects.bulk_create(seats_to_create)
            
            messages.success(request, f"Bus {bus.registration_number} added successfully! {len(seats_to_create)} seats generated automatically.")
            return redirect('system_admin:buses_list')
    else:
        form = BusForm()
    return render(request, 'system_admin/bus_form.html', {'form': form, 'title': 'Register New Bus'})

@login_required
@admin_required
def bus_edit(request, pk):
    bus = get_object_or_404(Bus, pk=pk)
    if request.method == 'POST':
        form = BusForm(request.POST, instance=bus)
        if form.is_valid():
            form.save()
            messages.success(request, "Bus details updated successfully!")
            return redirect('system_admin:buses_list')
    else:
        form = BusForm(instance=bus)
    return render(request, 'system_admin/bus_form.html', {'form': form, 'title': 'Edit Bus Details', 'bus': bus})

@login_required
@admin_required
@require_POST
def bus_delete(request, pk):
    bus = get_object_or_404(Bus, pk=pk)
    bus.delete()
    messages.success(request, "Bus record deleted successfully.")
    return redirect('system_admin:buses_list')

@login_required
@admin_required
def operator_create(request):
    if request.method == 'POST':
        form = BusOperatorForm(request.POST)
        if form.is_valid():
            op = form.save()
            messages.success(request, f"Bus Operator {op.name} added successfully!")
            return redirect('system_admin:buses_list')
    else:
        form = BusOperatorForm()
    return render(request, 'system_admin/operator_form.html', {'form': form, 'title': 'Add Bus Operator'})

@login_required
@admin_required
def operator_edit(request, pk):
    op = get_object_or_404(BusOperator, pk=pk)
    if request.method == 'POST':
        form = BusOperatorForm(request.POST, instance=op)
        if form.is_valid():
            form.save()
            messages.success(request, "Operator details updated successfully!")
            return redirect('system_admin:buses_list')
    else:
        form = BusOperatorForm(instance=op)
    return render(request, 'system_admin/operator_form.html', {'form': form, 'title': 'Edit Bus Operator Details', 'operator': op})

@login_required
@admin_required
@require_POST
def operator_delete(request, pk):
    op = get_object_or_404(BusOperator, pk=pk)
    op.delete()
    messages.success(request, "Bus Operator deleted successfully.")
    return redirect('system_admin:buses_list')

# --- Drivers Views ---

@login_required
@admin_required
def drivers_list(request):
    drivers = DriverProfile.objects.select_related('user', 'operator').all().order_by('id')
    
    context = {
        'drivers': drivers,
        'active_tab': 'drivers'
    }
    return render(request, 'system_admin/dashboard.html', context)

@login_required
@admin_required
def driver_create(request):
    if request.method == 'POST':
        form = DriverProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save()
            # Force user's profile role to DRIVER if not set
            if hasattr(profile.user, 'profile'):
                profile.user.profile.role = 'DRIVER'
                profile.user.profile.save()
            messages.success(request, f"Driver profile for {profile.user.username} created!")
            return redirect('system_admin:drivers_list')
    else:
        form = DriverProfileForm()
    return render(request, 'system_admin/driver_form.html', {'form': form, 'title': 'Register New Driver'})

@login_required
@admin_required
def driver_edit(request, pk):
    driver = get_object_or_404(DriverProfile, pk=pk)
    if request.method == 'POST':
        form = DriverProfileForm(request.POST, request.FILES, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, "Driver profile updated successfully!")
            return redirect('system_admin:drivers_list')
    else:
        form = DriverProfileForm(instance=driver)
    return render(request, 'system_admin/driver_form.html', {'form': form, 'title': 'Edit Driver Profile', 'driver': driver})

@login_required
@admin_required
@require_POST
def driver_delete(request, pk):
    driver = get_object_or_404(DriverProfile, pk=pk)
    driver.delete()
    messages.success(request, "Driver profile deleted successfully.")
    return redirect('system_admin:drivers_list')

@login_required
@admin_required
def notify_driver(request, pk):
    driver = get_object_or_404(DriverProfile, pk=pk)
    if request.method == 'POST':
        form = DriverNotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.driver = driver
            notification.save()
            messages.success(request, f"Notification sent to Driver {driver.user.get_full_name() or driver.user.username}!")
            return redirect('system_admin:drivers_list')
    else:
        form = DriverNotificationForm()
    return render(request, 'system_admin/notify_driver.html', {'form': form, 'driver': driver})

# --- Payments Views ---

@login_required
@admin_required
def payments_list(request):
    payments_qs = Payment.objects.select_related('booking__user').all().order_by('-payment_date')
    
    # Filters
    q = request.GET.get('q', '')
    if q:
        payments_qs = payments_qs.filter(
            Q(booking__user__username__icontains=q) |
            Q(transaction_id__icontains=q) |
            Q(sender_name__icontains=q) |
            Q(sender_number__icontains=q)
        )
        
    status = request.GET.get('status', '')
    if status:
        payments_qs = payments_qs.filter(status=status)
        
    paginator = Paginator(payments_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'q': q,
        'status': status,
        'active_tab': 'payments'
    }
    return render(request, 'system_admin/dashboard.html', context)

@login_required
@admin_required
@require_POST
def payment_status_update(request, pk, status):
    payment = get_object_or_404(Payment, pk=pk)
    if status in ['COMPLETED', 'FAILED', 'PENDING']:
        payment.status = status
        payment.save()
        messages.success(request, f"Payment for Booking #{payment.booking.id} updated to {status.lower()}.")
    else:
        messages.error(request, "Invalid payment status change.")
    return redirect(request.META.get('HTTP_REFERER', 'system_admin:payments_list'))

# --- Payment Detail View ---

@login_required
@admin_required
def payment_detail(request, pk):
    payment = get_object_or_404(Payment.objects.select_related('booking__user', 'booking__trip__route', 'booking__trip__bus__operator'), pk=pk)
    context = {
        'payment': payment,
        'active_tab': 'payments',
    }
    return render(request, 'system_admin/payment_detail.html', context)

# --- User Management Views ---

@login_required
@admin_required
def users_list(request):
    users_qs = User.objects.select_related('profile').all().order_by('-date_joined')
    
    # Filters
    q = request.GET.get('q', '')
    if q:
        users_qs = users_qs.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
        )
        
    paginator = Paginator(users_qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'q': q,
        'active_tab': 'users'
    }
    return render(request, 'system_admin/dashboard.html', context)

@login_required
@admin_required
@require_POST
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "You cannot deactivate your own account!")
    else:
        user.is_active = not user.is_active
        user.save()
        status_str = "activated" if user.is_active else "deactivated"
        messages.success(request, f"User {user.username} has been successfully {status_str}.")
    return redirect('system_admin:users_list')

@login_required
@admin_required
@require_POST
def user_toggle_staff(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "You cannot modify your own staff status!")
    else:
        user.is_staff = not user.is_staff
        user.save()
        status_str = "granted" if user.is_staff else "revoked"
        messages.success(request, f"Staff access {status_str} for user {user.username}.")
    return redirect('system_admin:users_list')

# --- Reviews Moderation Views ---

@login_required
@admin_required
def reviews_list(request):
    reviews_qs = Review.objects.select_related('booking__user', 'driver__user', 'bus__operator').all().order_by('-created_at')
    
    # Filters
    q = request.GET.get('q', '')
    if q:
        reviews_qs = reviews_qs.filter(
            Q(booking__user__username__icontains=q) |
            Q(comment__icontains=q) |
            Q(driver__user__username__icontains=q) |
            Q(bus__registration_number__icontains=q)
        )
        
    paginator = Paginator(reviews_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'q': q,
        'active_tab': 'reviews'
    }
    return render(request, 'system_admin/dashboard.html', context)

@login_required
@admin_required
@require_POST
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.delete()
    messages.success(request, "Customer review deleted (moderated) successfully.")
    return redirect('system_admin:reviews_list')

@login_required
@admin_required
def user_detail(request, pk):
    member = get_object_or_404(User.objects.select_related('profile'), pk=pk)
    bookings = member.bookings.select_related('trip__route').all().order_by('-booking_time')
    context = {
        'member': member,
        'bookings': bookings,
        'active_tab': 'users',
    }
    return render(request, 'system_admin/user_detail.html', context)

@login_required
@admin_required
def user_edit(request, pk):
    member = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserAdminForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f"User {member.username} was successfully updated.")
            return redirect('system_admin:user_detail', pk=member.pk)
    else:
        form = UserAdminForm(instance=member)
    
    context = {
        'form': form,
        'active_tab': 'users',
    }
    return render(request, 'system_admin/user_form.html', context)

@login_required
@admin_required
@require_POST
def user_delete(request, pk):
    member = get_object_or_404(User, pk=pk)
    if member == request.user:
        messages.error(request, "You cannot delete your own account!")
    else:
        username = member.username
        member.delete()
        messages.success(request, f"User {username} has been permanently deleted.")
    return redirect('system_admin:users_list')
