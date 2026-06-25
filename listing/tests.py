from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from listing.models import BusOperator, Bus, Route, Trip

class ListingSearchTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.operator = BusOperator.objects.create(
            name='Search Test Operator', 
            contact_email='search@test.com', 
            phone_number='12345'
        )
        self.route = Route.objects.create(origin='CityX', destination='CityY')
        self.bus = Bus.objects.create(
            operator=self.operator,
            registration_number='BUS-TEST-SEARCH',
            capacity=10
        )
        
        # Scheduled trip (should appear in results)
        self.scheduled_trip = Trip.objects.create(
            bus=self.bus,
            route=self.route,
            departure_time=timezone.now() + timezone.timedelta(days=1),
            arrival_time=timezone.now() + timezone.timedelta(days=1, hours=2),
            price=30.00,
            status='SCHEDULED'
        )
        
        # Started trip (should be excluded from results)
        self.started_trip = Trip.objects.create(
            bus=self.bus,
            route=self.route,
            departure_time=timezone.now() + timezone.timedelta(days=1),
            arrival_time=timezone.now() + timezone.timedelta(days=1, hours=2),
            price=30.00,
            status='STARTED'
        )

    def test_search_excludes_started_trips(self):
        """Verify that started trips are not returned in the search results."""
        response = self.client.get(reverse('listing:search'), {
            'origin': 'CityX',
            'destination': 'CityY'
        })
        self.assertEqual(response.status_code, 200)
        
        trips_in_context = response.context['trips']
        
        # Scheduled trip should be in results
        self.assertTrue(any(t.id == self.scheduled_trip.id for t in trips_in_context))
        
        # Started trip should NOT be in results
        self.assertFalse(any(t.id == self.started_trip.id for t in trips_in_context))
