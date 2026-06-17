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
    
    stripe_secret = getattr(settings, 'STRIPE_SECRET_KEY', None)
    stripe_public = getattr(settings, 'STRIPE_PUBLISHABLE_KEY', None)
    
    is_placeholder = (
        not stripe_secret or stripe_secret.strip() == "" or "placeholder" in stripe_secret.lower() or "..." in stripe_secret or
        not stripe_public or stripe_public.strip() == "" or "placeholder" in stripe_public.lower() or "..." in stripe_public
    )
    
    if is_placeholder:
        if settings.DEBUG:
            return render(request, 'payments/mock_checkout.html', {
                'booking': booking,
                'publishable_key': getattr(settings, 'STRIPE_PUBLISHABLE_KEY', None)
            })
        else:
            return HttpResponse("Error: Stripe Secret Key is not configured in settings/environment.", status=500)
            
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

@login_required
def mock_confirm_payment(request, booking_id):
    if not settings.DEBUG:
        return HttpResponse("Action not allowed in production.", status=403)
        
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Update booking status
    booking.status = 'CONFIRMED'
    booking.save()
    
    # Create the payment record
    Payment.objects.create(
        booking=booking,
        amount=booking.total_amount,
        transaction_id=f'mock_txn_{booking.id}_{request.user.id}',
        payment_method='Stripe (Mock)',
        status='COMPLETED'
    )
    
    return redirect('payments:success')


def payment_success(request):
    session_id = request.GET.get('session_id')
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            booking_id = getattr(session, 'client_reference_id', None)
            if booking_id:
                booking = Booking.objects.get(id=booking_id)
                # Check if a payment already exists for this booking to prevent duplicate confirmation
                if not Payment.objects.filter(booking=booking).exists():
                    booking.status = 'CONFIRMED'
                    booking.save()
                    
                    Payment.objects.create(
                        booking=booking,
                        amount=booking.total_amount,
                        transaction_id=getattr(session, 'payment_intent', None) or session_id,
                        payment_method='Stripe',
                        status='COMPLETED'
                    )
        except Exception:
            # Silently fallback to rendering success template if API call fails (e.g. invalid test session id)
            pass
            
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
        
        booking_id = getattr(session, 'client_reference_id', None)
        if booking_id:
            try:
                booking = Booking.objects.get(id=booking_id)
                booking.status = 'CONFIRMED'
                booking.save()
                
                Payment.objects.create(
                    booking=booking,
                    amount=booking.total_amount,
                    transaction_id=getattr(session, 'payment_intent', None),
                    payment_method='Stripe',
                    status='COMPLETED'
                )
            except Booking.DoesNotExist:
                pass
                
    return HttpResponse(status=200)

@login_required
def choose_payment_method(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, 'payments/choose_payment.html', {'booking': booking})

@login_required
def local_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if request.method == 'POST':
        sender_number = request.POST.get('sender_number', '')
        sender_name = request.POST.get('sender_name', '')
        transaction_id = request.POST.get('transaction_id', f'local_{booking.id}_{request.user.id}')
        payment_provider = request.POST.get('payment_provider', 'Mobile Money')
        
        Payment.objects.create(
            booking=booking,
            amount=booking.total_amount,
            transaction_id=transaction_id,
            payment_method=payment_provider,
            status='PENDING',
            sender_number=sender_number,
            sender_name=sender_name
        )
        booking.status = 'PENDING'
        booking.save()
        return redirect('payments:local_success', booking_id=booking.id)
        
    return render(request, 'payments/local_payment.html', {'booking': booking})

@login_required
def local_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, 'payments/local_success.html', {'booking': booking})
