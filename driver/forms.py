from django import forms
from .models import DriverProfile
from listing.models import Trip

class DriverProfileForm(forms.ModelForm):
    class Meta:
        model = DriverProfile
        fields = ['phone', 'address', 'emergency_contact', 'photo']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
        }

class DelayReportForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['delay_minutes', 'delay_reason']
        widgets = {
            'delay_minutes': forms.NumberInput(attrs={'min': 1, 'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Minutes (e.g. 30)'}),
            'delay_reason': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Reason for delay (e.g. Heavy traffic on Route 1, engine check)'}),
        }
