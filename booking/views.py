from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Booking, Passenger
from listing.models import Trip, Seat, Route

def home_view(request):
    # Fetch data for the search dropdowns on the landing page
    origins = Route.objects.values_list('origin', flat=True).distinct()
    destinations = Route.objects.values_list('destination', flat=True).distinct()
    return render(request, 'booking/home.html', {'origins': origins, 'destinations': destinations})

@login_required
def book_trip_view(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    
    if request.method == 'POST':
        seat_ids = request.POST.getlist('seats')
        
        if not seat_ids:
            messages.error(request, "Please select at least one seat.")
            return redirect('listing:trip_detail', pk=trip.id)
            
        seats = Seat.objects.filter(id__in=seat_ids)
        
        # Verify seats belong to this bus and are available
        for seat in seats:
            if seat.bus != trip.bus:
                messages.error(request, "Invalid seat selection.")
                return redirect('listing:trip_detail', pk=trip.id)
            if not trip.is_seat_available(seat):
                messages.error(request, f"Seat {seat.seat_number} is no longer available.")
                return redirect('listing:trip_detail', pk=trip.id)
        
        # Save seat IDs in session to be used in passenger details step
        request.session['selected_seats'] = seat_ids
        return redirect('booking:passenger_details', trip_id=trip.id)
        
    return redirect('listing:trip_detail', pk=trip.id)

@login_required
def passenger_details_view(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    seat_ids = request.session.get('selected_seats', [])
    
    if not seat_ids:
        messages.error(request, "Session expired or no seats selected.")
        return redirect('listing:trip_detail', pk=trip.id)
        
    seats = Seat.objects.filter(id__in=seat_ids)
    
    if request.method == 'POST':
        contact_email = request.POST.get('contact_email')
        contact_phone_raw = request.POST.get('contact_phone_raw')
        country_code = request.POST.get('country_code', '+252')
        
        contact_phone = f"{country_code} {contact_phone_raw}" if contact_phone_raw else ""
        
        if not contact_email or not contact_phone_raw:
            messages.error(request, "Please provide contact details.")
            return render(request, 'booking/passenger_details.html', {'trip': trip, 'seats': seats})
            
        # Create pending booking
        booking = Booking.objects.create(
            user=request.user,
            trip=trip,
            status='PENDING',
            contact_email=contact_email,
            contact_phone=contact_phone
        )
        
        try:
            booking.book_seats(seats)
        except ValidationError as e:
            booking.delete()
            messages.error(request, str(e.message) if hasattr(e, 'message') else str(e))
            return redirect('listing:trip_detail', pk=trip.id)
            
        # Create passenger objects
        for seat in seats:
            name = request.POST.get(f'name_{seat.id}')
            age = request.POST.get(f'age_{seat.id}')
            gender = request.POST.get(f'gender_{seat.id}')
            
            if name and age and gender:
                Passenger.objects.create(
                    booking=booking,
                    seat=seat,
                    name=name,
                    age=age,
                    gender=gender
                )
                
        # Clear session
        if 'selected_seats' in request.session:
            del request.session['selected_seats']
            
        messages.success(request, "Your booking has been placed successfully! Redirecting to payment...")
        return redirect('payments:choose_payment_method', booking_id=booking.id)
        
    return render(request, 'booking/passenger_details.html', {'trip': trip, 'seats': seats})

@login_required
def my_bookings_view(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_time')
    return render(request, 'booking/my_bookings.html', {'bookings': bookings})
