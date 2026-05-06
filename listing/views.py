from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from .models import Trip, Route, BusOperator

def trip_search_view(request):
    origin = request.GET.get('origin', '')
    destination = request.GET.get('destination', '')
    date_str = request.GET.get('date', '')
    time_filter = request.GET.getlist('time_filter') # e.g. ['morning', 'afternoon']
    operator_filter = request.GET.getlist('operator_filter') # e.g. ['1', '3']

    trips = Trip.objects.filter(departure_time__gte=timezone.now()).order_by('departure_time')

    if origin:
        trips = trips.filter(route__origin__icontains=origin)
    if destination:
        trips = trips.filter(route__destination__icontains=destination)
    if date_str:
        trips = trips.filter(departure_time__date=date_str)

    # Time Filters
    if time_filter:
        time_queries = Q()
        for tf in time_filter:
            if tf == 'morning':
                time_queries |= Q(departure_time__hour__gte=6, departure_time__hour__lt=12)
            elif tf == 'afternoon':
                time_queries |= Q(departure_time__hour__gte=12, departure_time__hour__lt=18)
            elif tf == 'evening':
                time_queries |= Q(departure_time__hour__gte=18, departure_time__hour__lt=24)
            elif tf == 'night':
                time_queries |= Q(departure_time__hour__gte=0, departure_time__hour__lt=6)
        trips = trips.filter(time_queries)
        
    # Operator Filter
    if operator_filter:
        trips = trips.filter(bus__operator__id__in=operator_filter)

    # Calculate available seats for display
    for trip in trips:
        trip.available_seats_count = trip.get_available_seats().count()

    origins = Route.objects.values_list('origin', flat=True).distinct()
    destinations = Route.objects.values_list('destination', flat=True).distinct()
    operators = BusOperator.objects.all()

    context = {
        'trips': trips,
        'search_origin': origin,
        'search_destination': destination,
        'search_date': date_str,
        'selected_times': time_filter,
        'selected_operators': [int(o) for o in operator_filter if o.isdigit()],
        'origins': origins,
        'destinations': destinations,
        'operators': operators,
    }
    return render(request, 'listing/search_results.html', context)

def trip_detail_view(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    
    # We need to present the seats nicely. Assuming seats are named like 1A, 1B, 1C, 1D.
    # For a simple representation, we'll just pass all seats and their availability.
    all_seats = trip.bus.seats.all().order_by('id')
    booked_seat_ids = trip.get_booked_seats().values_list('id', flat=True)
    
    seat_data = []
    for seat in all_seats:
        seat_data.append({
            'seat': seat,
            'is_booked': seat.id in booked_seat_ids
        })
        
    context = {
        'trip': trip,
        'seat_data': seat_data,
        'available_count': trip.get_available_seats().count(),
    }
    return render(request, 'listing/trip_detail.html', context)
