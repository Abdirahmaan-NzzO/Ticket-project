from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from booking.models import Booking
from .models import Review
from .forms import ReviewForm

@login_required
def create_review(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if hasattr(booking, 'review'):
        messages.info(request, "You have already reviewed this booking.")
        return redirect('booking:my_bookings')
    
    if booking.status != 'CONFIRMED':
        messages.error(request, "You can only review confirmed bookings.")
        return redirect('booking:my_bookings')
        
    if booking.trip.status != 'COMPLETED' and booking.trip.arrival_time > timezone.now():
        messages.error(request, "You can only review trips that have been completed.")
        return redirect('booking:my_bookings')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            if not booking.trip.bus.driver:
                messages.error(request, "No driver is assigned to this bus. Cannot leave review.")
                return redirect('booking:my_bookings')
                
            review = form.save(commit=False)
            review.booking = booking
            review.bus = booking.trip.bus
            review.driver = booking.trip.bus.driver
            review.save()
            messages.success(request, "Thank you for your review!")
            return redirect('booking:my_bookings')
    else:
        form = ReviewForm()

    return render(request, 'reviews/create_review.html', {
        'form': form,
        'booking': booking
    })
