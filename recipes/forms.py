from django import forms
from .models import RecipeRequest

class RecipeRequestForm(forms.ModelForm):
    """
    This form links the RecipeRequest model to the HTML template.
    We add the 'form-control' class here so it matches your HTML styling.
    """
    class Meta:
        model = RecipeRequest
        fields = ['cuisine', 'allergies', 'ingredients']
        widgets = {
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
        }
        help_texts = {
            'allergies': 'Comma-separated list of allergies to avoid.',
            'ingredients': 'Comma-separated list of ingredients you have or want to use.',
        }