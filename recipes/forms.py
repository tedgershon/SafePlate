from django import forms
from .models import RecipeRequest


class RecipeRequestForm(forms.ModelForm):
    """Form for submitting recipe requests"""
    
    class Meta:
        model = RecipeRequest
        fields = ['cuisine', 'allergies', 'ingredients']
        widgets = {
            'cuisine': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Italian, Chinese, Mexican'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g., nuts, shellfish, dairy'}),
            'ingredients': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g., chicken, tomatoes, basil'}),
        }
        labels = {
            'cuisine': 'Cuisine Type',
            'allergies': 'Allergies (comma-separated)',
            'ingredients': 'Available Ingredients (comma-separated)',
        }
