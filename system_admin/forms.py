from django import forms
from django.contrib.auth.models import User
from listing.models import Trip, Route, Bus, BusOperator, Amenity
from driver.models import DriverProfile, DriverNotification

class BaseAdminForm(forms.ModelForm):
    """Base form that auto-applies Tailwind CSS styles to fields."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.update({'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500 h-4 w-4'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({
                    'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200',
                    'rows': 3
                })
            else:
                field.widget.attrs.update({'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200'})

class TripForm(BaseAdminForm):
    class Meta:
        model = Trip
        fields = ['bus', 'route', 'departure_time', 'arrival_time', 'price', 'status', 'delay_minutes', 'delay_reason']
        widgets = {
            'departure_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'arrival_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class RouteForm(BaseAdminForm):
    class Meta:
        model = Route
        fields = ['origin', 'destination']

class BusForm(BaseAdminForm):
    class Meta:
        model = Bus
        fields = ['operator', 'registration_number', 'capacity', 'bus_type', 'amenities', 'driver']
        widgets = {
            'amenities': forms.CheckboxSelectMultiple(),
        }

class BusOperatorForm(BaseAdminForm):
    class Meta:
        model = BusOperator
        fields = ['name', 'contact_email', 'phone_number']

class DriverProfileForm(BaseAdminForm):
    class Meta:
        model = DriverProfile
        fields = ['user', 'operator', 'license_number', 'phone', 'address', 'experience_years', 'emergency_contact', 'photo', 'status']

class DriverNotificationForm(forms.ModelForm):
    class Meta:
        model = DriverNotification
        fields = ['title', 'message']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Notification Title'}),
            'message': forms.Textarea(attrs={'placeholder': 'Type your message here...', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({
                    'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200',
                    'rows': 4
                })
            else:
                field.widget.attrs.update({'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200'})
