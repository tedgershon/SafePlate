from django import forms
from .models import RecipeRequest


class RecipeRequestForm(forms.ModelForm):
    """Form for submitting recipe requests"""
    
    class Meta:
        model = RecipeRequest
        fields = ['cuisine', 'allergies', 'ingredients']
        widgets = {
<<<<<<< HEAD
            'cuisine': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Italian, Chinese, Mexican (optional)'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g., nuts, shellfish, dairy (optional)'}),
            'ingredients': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g., chicken, tomatoes, basil (optional)'}),
        }
        labels = {
            'cuisine': 'Cuisine Type (Optional)',
            'allergies': 'Allergies (Optional, comma-separated)',
            'ingredients': 'Available Ingredients (Optional, comma-separated)',
=======
            'cuisine': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., Italian, Mexican, Japanese'
            }),
            'allergies': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., nuts, dairy, shellfish'
            }),
            'ingredients': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'e.g., chicken, tomatoes, basil'
            }),
>>>>>>> 61656806e738e07c5889ce7e809eb9f98bac46d5
        }
