from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import UserProfile
from listing.models import BusOperator, Bus, Route, Seat, Trip
from booking.models import Booking, Passenger
from driver.models import DriverProfile, DriverNotification
from django.utils import timezone

class DriverPanelTests(TestCase):
    def setUp(self):
        # Create standard Client
        self.client = Client()
        
        # Create test users
        self.driver_user = User.objects.create_user(username='driveruser', password='password123', email='driver@test.com')
        self.passenger_user = User.objects.create_user(username='passuser', password='password123', email='pass@test.com')
        
        # Central UserProfile roles are set automatically by signals in some setups, 
        # but let's explicitly get or create/update it.
        driver_profile, _ = UserProfile.objects.get_or_create(user=self.driver_user)
        driver_profile.role = 'DRIVER'
        driver_profile.save()
        
        pass_profile, _ = UserProfile.objects.get_or_create(user=self.passenger_user)
        pass_profile.role = 'PASSENGER'
        pass_profile.save()
        
        # Create DriverProfile
        self.driver_details = DriverProfile.objects.create(
            user=self.driver_user,
            license_number='DL-998877',
            phone='1234567890',
            status='ACTIVE'
        )
        
        # Setup Bus database
        self.operator = BusOperator.objects.create(name='Test Operator', contact_email='op@test.com', phone_number='09876')
        self.route = Route.objects.create(origin='CityA', destination='CityB')
        self.bus = Bus.objects.create(operator=self.operator, registration_number='BUS-1111', capacity=10, driver=self.driver_details)
        self.seat = Seat.objects.create(bus=self.bus, seat_number='1A')
        self.trip = Trip.objects.create(
            bus=self.bus, 
            route=self.route, 
            departure_time=timezone.now() + timezone.timedelta(days=1), 
            arrival_time=timezone.now() + timezone.timedelta(days=1, hours=2),
            price=20.00
        )
        
        # Setup Booking database
        self.booking = Booking.objects.create(
            user=self.passenger_user,
            trip=self.trip,
            status='CONFIRMED',
            total_amount=20.00
        )
        self.passenger = Passenger.objects.create(
            booking=self.booking,
            seat=self.seat,
            name='John Doe',
            age=30,
            gender='M'
        )

    def test_unauthenticated_access_denied(self):
        """Verify anonymous user is redirected to login page."""
        response = self.client.get(reverse('driver:dashboard'))
        self.assertRedirects(response, '/accounts/login/?next=/driver/dashboard/')

    def test_passenger_access_denied(self):
        """Verify passengers get a 403 Forbidden."""
        self.client.login(username='passuser', password='password123')
        response = self.client.get(reverse('driver:dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_driver_access_allowed(self):
        """Verify authorized drivers can access dashboard."""
        self.client.login(username='driveruser', password='password123')
        response = self.client.get(reverse('driver:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'DL-998877')

    def test_driver_status_update(self):
        """Test toggling driver duty status."""
        self.client.login(username='driveruser', password='password123')
        # Change status to INACTIVE
        response = self.client.post(reverse('driver:status_update'), {'status': 'INACTIVE'})
        self.driver_details.refresh_from_db()
        self.assertEqual(self.driver_details.status, 'INACTIVE')
        
        # Change status back to ACTIVE
        response = self.client.post(reverse('driver:status_update'), {'status': 'ACTIVE'})
        self.driver_details.refresh_from_db()
        self.assertEqual(self.driver_details.status, 'ACTIVE')

    def test_start_and_complete_trip(self):
        """Test the lifecycle of starting and completing a trip."""
        self.client.login(username='driveruser', password='password123')
        
        # Start Trip
        response = self.client.post(reverse('driver:start_trip', args=[self.trip.id]))
        self.trip.refresh_from_db()
        self.driver_details.refresh_from_db()
        self.assertEqual(self.trip.status, 'STARTED')
        self.assertEqual(self.driver_details.status, 'ON_TRIP')
        
        # Complete Trip
        response = self.client.post(reverse('driver:complete_trip', args=[self.trip.id]))
        self.trip.refresh_from_db()
        self.driver_details.refresh_from_db()
        self.assertEqual(self.trip.status, 'COMPLETED')
        self.assertEqual(self.driver_details.status, 'ACTIVE')

    def test_report_delay(self):
        """Test reporting a trip delay."""
        self.client.login(username='driveruser', password='password123')
        
        delay_data = {
            'delay_minutes': 45,
            'delay_reason': 'Accident on highway'
        }
        response = self.client.post(reverse('driver:report_delay', args=[self.trip.id]), delay_data)
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.status, 'DELAYED')
        self.assertEqual(self.trip.delay_minutes, 45)
        self.assertEqual(self.trip.delay_reason, 'Accident on highway')
        
        # Verify notification created
        notifications = DriverNotification.objects.filter(driver=self.driver_details)
        self.assertEqual(notifications.count(), 1)
        self.assertIn('45 minutes', notifications.first().message)

    def test_passenger_boarding_status_update(self):
        """Test driver marking a passenger as boarded or no-show."""
        self.client.login(username='driveruser', password='password123')
        
        # Start the trip first so checking passengers becomes active
        self.trip.status = 'STARTED'
        self.trip.save()
        
        # Mark as BOARDED
        response = self.client.post(reverse('driver:passenger_board', args=[self.passenger.id, 'BOARDED']))
        self.passenger.refresh_from_db()
        self.assertEqual(self.passenger.boarding_status, 'BOARDED')
        
        # Mark as NO_SHOW
        response = self.client.post(reverse('driver:passenger_board', args=[self.passenger.id, 'NO_SHOW']))
        self.passenger.refresh_from_db()
        self.assertEqual(self.passenger.boarding_status, 'NO_SHOW')

    def test_driver_operator_matching_validation(self):
        """Verify that a bus cannot be saved with a driver belonging to a different operator."""
        from django.core.exceptions import ValidationError
        
        # Create a different operator
        different_operator = BusOperator.objects.create(name='Different Operator', contact_email='diff@test.com', phone_number='1111')
        
        # Match driver to the different operator
        self.driver_details.operator = different_operator
        self.driver_details.save()
        
        # The bus belongs to self.operator. Assigning self.driver_details (which now has different_operator) should fail validation
        self.bus.driver = self.driver_details
        
        with self.assertRaises(ValidationError):
            self.bus.clean()
