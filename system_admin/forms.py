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

class UserAdminForm(BaseAdminForm):
    role = forms.ChoiceField(
        choices=(
            ('ADMIN', 'Admin'),
            ('DRIVER', 'Driver'),
            ('PASSENGER', 'Passenger'),
        ),
        required=True
    )
    phone_number = forms.CharField(required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            from accounts.models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=self.instance)
            self.fields['role'].initial = profile.role
            self.fields['phone_number'].initial = profile.phone_number
            self.fields['address'].initial = profile.address

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            from accounts.models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = self.cleaned_data['role']
            profile.phone_number = self.cleaned_data.get('phone_number', '')
            profile.address = self.cleaned_data.get('address', '')
            profile.save()
        return user
