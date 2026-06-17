from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from booking.models import Booking
from listing.models import BusOperator, Bus, Route, Seat, Trip
from driver.models import DriverProfile
from reviews.models import Review

class ReviewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='reviewer', password='password123')
        
        self.operator = BusOperator.objects.create(name='Test Operator', contact_email='op@test.com', phone_number='09876')
        self.route = Route.objects.create(origin='CityA', destination='CityB')
        self.bus = Bus.objects.create(operator=self.operator, registration_number='BUS-2222', capacity=10)
        self.seat = Seat.objects.create(bus=self.bus, seat_number='2A')
        
        # Create a driver and assign to the bus
        self.driver_user = User.objects.create_user(username='driver_user', password='password123')
        self.driver_profile = DriverProfile.objects.create(
            user=self.driver_user,
            operator=self.operator,
            license_number='DL-9999',
            phone='12345678'
        )
        self.bus.driver = self.driver_profile
        self.bus.save()
        
        self.trip = Trip.objects.create(
            bus=self.bus,
            route=self.route,
            departure_time=timezone.now() - timezone.timedelta(hours=5),
            arrival_time=timezone.now() - timezone.timedelta(hours=3),
            price=20.00,
            status='SCHEDULED'
        )
        
        self.booking = Booking.objects.create(
            user=self.user,
            trip=self.trip,
            status='CONFIRMED',
            total_amount=20.00
        )
        self.booking.seats.add(self.seat)

    def test_can_be_reviewed_past_trip_with_driver(self):
        # Booking is confirmed, trip is in the past, bus has a driver -> can be reviewed
        self.assertTrue(self.booking.can_be_reviewed)

    def test_cannot_be_reviewed_if_pending(self):
        self.booking.status = 'PENDING'
        self.booking.save()
        self.assertFalse(self.booking.can_be_reviewed)

    def test_cannot_be_reviewed_if_no_driver(self):
        self.bus.driver = None
        self.bus.save()
        self.booking.refresh_from_db()
        self.assertFalse(self.booking.can_be_reviewed)

    def test_cannot_be_reviewed_if_future_trip(self):
        self.trip.departure_time = timezone.now() + timezone.timedelta(days=1)
        self.trip.arrival_time = timezone.now() + timezone.timedelta(days=1, hours=2)
        self.trip.save()
        self.booking.refresh_from_db()
        self.assertFalse(self.booking.can_be_reviewed)

    def test_create_review_view_success(self):
        self.client.login(username='reviewer', password='password123')
        # GET form
        response = self.client.get(reverse('reviews:create_review', args=[self.booking.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reviews/create_review.html')
        
        # POST review
        post_data = {
            'rating': 5,
            'comment': 'Amazing trip!'
        }
        response = self.client.post(reverse('reviews:create_review', args=[self.booking.id]), data=post_data)
        self.assertRedirects(response, reverse('booking:my_bookings'))
        
        # Check review was created
        self.assertTrue(Review.objects.filter(booking=self.booking).exists())
        review = Review.objects.get(booking=self.booking)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Amazing trip!')
        self.assertEqual(review.bus, self.bus)
        self.assertEqual(review.driver, self.driver_profile)

    def test_create_review_view_redirect_if_no_driver(self):
        self.bus.driver = None
        self.bus.save()
        self.client.login(username='reviewer', password='password123')
        
        # Should redirect immediately on GET
        response = self.client.get(reverse('reviews:create_review', args=[self.booking.id]))
        self.assertRedirects(response, reverse('booking:my_bookings'))
