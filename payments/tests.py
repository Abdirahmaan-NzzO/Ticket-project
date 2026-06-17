from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from booking.models import Booking
from listing.models import BusOperator, Bus, Route, Seat, Trip
from .models import Payment

class PaymentsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='paymentuser', password='password123', email='pay@test.com')
        
        self.operator = BusOperator.objects.create(name='Test Operator', contact_email='op@test.com', phone_number='09876')
        self.route = Route.objects.create(origin='CityA', destination='CityB')
        self.bus = Bus.objects.create(operator=self.operator, registration_number='BUS-1111', capacity=10)
        self.seat = Seat.objects.create(bus=self.bus, seat_number='1A')
        self.trip = Trip.objects.create(
            bus=self.bus, 
            route=self.route, 
            departure_time=timezone.now() + timezone.timedelta(days=1), 
            arrival_time=timezone.now() + timezone.timedelta(days=1, hours=2),
            price=20.00
        )
        self.booking = Booking.objects.create(
            user=self.user,
            trip=self.trip,
            status='PENDING',
            total_amount=20.00
        )
        self.booking.seats.add(self.seat)

    @override_settings(STRIPE_SECRET_KEY='sk_test_...', STRIPE_PUBLISHABLE_KEY='pk_test_...', DEBUG=True)
    def test_create_checkout_session_with_placeholder_keys_renders_mock_checkout(self):
        self.client.login(username='paymentuser', password='password123')
        response = self.client.get(reverse('payments:create_checkout_session', args=[self.booking.id]))
        # With placeholder keys, it should render the mock checkout portal instead of calling Stripe
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/mock_checkout.html')
        self.assertContains(response, 'Simulation Mode')
        self.assertContains(response, 'Confirm Mock Payment')

    @override_settings(STRIPE_SECRET_KEY='', STRIPE_PUBLISHABLE_KEY='', DEBUG=True)
    def test_create_checkout_session_with_empty_keys_renders_mock_checkout(self):
        self.client.login(username='paymentuser', password='password123')
        response = self.client.get(reverse('payments:create_checkout_session', args=[self.booking.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/mock_checkout.html')

    @override_settings(STRIPE_SECRET_KEY='placeholder_key', STRIPE_PUBLISHABLE_KEY='placeholder_pub', DEBUG=True)
    def test_create_checkout_session_with_explicit_placeholder_key_renders_mock_checkout(self):
        self.client.login(username='paymentuser', password='password123')
        response = self.client.get(reverse('payments:create_checkout_session', args=[self.booking.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/mock_checkout.html')

    def test_payment_completed_syncs_booking_confirmed(self):
        payment = Payment.objects.create(
            booking=self.booking,
            amount=self.booking.total_amount,
            payment_method='Mobile Money',
            status='PENDING'
        )
        payment.status = 'COMPLETED'
        payment.save()
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'CONFIRMED')

    def test_booking_confirmed_syncs_payment_completed(self):
        payment = Payment.objects.create(
            booking=self.booking,
            amount=self.booking.total_amount,
            payment_method='Mobile Money',
            status='PENDING'
        )
        self.booking.status = 'CONFIRMED'
        self.booking.save()
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'COMPLETED')

    def test_payment_failed_syncs_booking_cancelled(self):
        payment = Payment.objects.create(
            booking=self.booking,
            amount=self.booking.total_amount,
            payment_method='Mobile Money',
            status='PENDING'
        )
        payment.status = 'FAILED'
        payment.save()
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'CANCELLED')

    from unittest.mock import patch

    @patch('stripe.checkout.Session.retrieve')
    def test_payment_success_with_session_id_confirms_booking(self, mock_retrieve):
        from unittest.mock import MagicMock
        mock_session = MagicMock()
        mock_session.client_reference_id = str(self.booking.id)
        mock_session.payment_intent = 'pi_test_12345'
        mock_retrieve.return_value = mock_session
        
        self.client.login(username='paymentuser', password='password123')
        
        # Initially booking status is PENDING and no Payment exists
        self.assertEqual(self.booking.status, 'PENDING')
        self.assertFalse(Payment.objects.filter(booking=self.booking).exists())
        
        response = self.client.get(reverse('payments:success') + '?session_id=cs_test_abc')
        self.assertEqual(response.status_code, 200)
        
        # Booking should be updated to CONFIRMED
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'CONFIRMED')
        
        # Payment object should be created
        payment = Payment.objects.get(booking=self.booking)
        self.assertEqual(payment.amount, self.booking.total_amount)
        self.assertEqual(payment.payment_method, 'Stripe')
        self.assertEqual(payment.status, 'COMPLETED')
        self.assertEqual(payment.transaction_id, 'pi_test_12345')

    @patch('stripe.checkout.Session.retrieve')
    def test_payment_success_with_session_id_idempotent(self, mock_retrieve):
        from unittest.mock import MagicMock
        mock_session = MagicMock()
        mock_session.client_reference_id = str(self.booking.id)
        mock_session.payment_intent = 'pi_test_12345'
        mock_retrieve.return_value = mock_session

        self.client.login(username='paymentuser', password='password123')
        
        # Create an existing payment
        Payment.objects.create(
            booking=self.booking,
            amount=self.booking.total_amount,
            transaction_id='pi_test_12345',
            payment_method='Stripe',
            status='COMPLETED'
        )
        self.booking.status = 'CONFIRMED'
        self.booking.save()
        
        response = self.client.get(reverse('payments:success') + '?session_id=cs_test_abc')
        self.assertEqual(response.status_code, 200)
        
        # Confirm that no duplicate payment object is created
        self.assertEqual(Payment.objects.filter(booking=self.booking).count(), 1)


