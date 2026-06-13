from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'w-full pl-3 pr-10 py-3 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-xl'
            }),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full p-4 border border-gray-300 rounded-xl focus:ring-blue-500 focus:border-blue-500 text-gray-800 placeholder-gray-400',
                'placeholder': 'Share details of your experience with the driver, the bus condition, and the overall journey...'
            }),
        }
