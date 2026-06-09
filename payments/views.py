import stripe
from django.conf import settings
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from booking.models import Booking
from .models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def create_checkout_session(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    domain_url = request.build_absolute_uri('/')[:-1]
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(booking.total_amount * 100),
                    'product_data': {
                        'name': f'Bus Ticket Booking #{booking.id}',
                        'description': f'Trip from {booking.trip.route.origin} to {booking.trip.route.destination}',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=domain_url + reverse('payments:success') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + reverse('payments:cancel'),
            client_reference_id=str(booking.id),
            metadata={'booking_id': booking.id}
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")

def payment_success(request):
    return render(request, 'payments/success.html')

def payment_cancel(request):
    return render(request, 'payments/cancel.html')

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None
    
    endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)

    try:
        if endpoint_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        else:
            import json
            event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        booking_id = session.get('client_reference_id')
        if booking_id:
            try:
                booking = Booking.objects.get(id=booking_id)
                booking.status = 'CONFIRMED'
                booking.save()
                
                Payment.objects.create(
                    booking=booking,
                    amount=booking.total_amount,
                    transaction_id=session.get('payment_intent'),
                    payment_method='Stripe',
                    status='COMPLETED'
                )
            except Booking.DoesNotExist:
                pass
                
    return HttpResponse(status=200)
