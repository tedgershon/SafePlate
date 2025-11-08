from django import forms
from .models import RecipeRequest


class RecipeRequestForm(forms.ModelForm):
    """Form for submitting recipe requests"""
    
    # Common cuisines as choices
    CUISINE_CHOICES = [
        ('italian', 'Italian'),
        ('mexican', 'Mexican'),
        ('chinese', 'Chinese'),
        ('japanese', 'Japanese'),
        ('indian', 'Indian'),
        ('thai', 'Thai'),
        ('french', 'French'),
        ('american', 'American'),
        ('mediterranean', 'Mediterranean'),
        ('korean', 'Korean'),
    ]
    
    # Common allergies as choices
    ALLERGY_CHOICES = [
        ('nuts', 'Nuts'),
        ('peanuts', 'Peanuts'),
        ('dairy', 'Dairy'),
        ('eggs', 'Eggs'),
        ('soy', 'Soy'),
        ('wheat', 'Wheat/Gluten'),
        ('shellfish', 'Shellfish'),
        ('fish', 'Fish'),
        ('sesame', 'Sesame'),
        ('garlic', 'Garlic'),
        ('onion', 'Onion'),
    ]
    
    # Override fields with custom widgets
    cuisine_choices = forms.MultipleChoiceField(
        choices=CUISINE_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'cuisine-checkbox'}),
        required=False,
        label='Cuisine (Select up to 2)'
    )
    
    cuisine_other = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Specify other cuisine(s)'
        }),
        label='Other Cuisine'
    )
    
    allergy_choices = forms.MultipleChoiceField(
        choices=ALLERGY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'allergy-checkbox'}),
        required=False,
        label='Allergies (Select all that apply)'
    )
    
    allergy_other = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Specify other allergies'
        }),
        label='Other Allergies'
    )
    
    class Meta:
        model = RecipeRequest
        fields = ['ingredients']
        widgets = {
            'ingredients': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'e.g., chicken, tomatoes, basil'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Reorder fields
        self.fields['ingredients'].label = 'Available Ingredients'
    
    def clean_cuisine_choices(self):
        """Validate that no more than 2 cuisines are selected"""
        cuisines = self.cleaned_data.get('cuisine_choices', [])
        if len(cuisines) > 2:
            raise forms.ValidationError('Please select a maximum of 2 cuisines.')
        return cuisines
    
    def clean(self):
        """Combine checkbox selections with 'Other' text inputs"""
        cleaned_data = super().clean()
        
        # Combine cuisines
        cuisine_list = list(cleaned_data.get('cuisine_choices', []))
        cuisine_other = cleaned_data.get('cuisine_other', '').strip()
        if cuisine_other:
            cuisine_list.append(cuisine_other)
        
        # Validate max 2 cuisines total
        if len(cuisine_list) > 2:
            raise forms.ValidationError('Please select or enter a maximum of 2 cuisines in total.')
        
        cleaned_data['cuisine'] = ', '.join(cuisine_list) if cuisine_list else ''
        
        # Combine allergies
        allergy_list = list(cleaned_data.get('allergy_choices', []))
        allergy_other = cleaned_data.get('allergy_other', '').strip()
        if allergy_other:
            allergy_list.append(allergy_other)
        
        cleaned_data['allergies'] = ', '.join(allergy_list) if allergy_list else ''
        
        return cleaned_data
    
    def save(self, commit=True):
        """Override save to set cuisine and allergies from cleaned_data"""
        instance = super().save(commit=False)
        instance.cuisine = self.cleaned_data.get('cuisine', '')
        instance.allergies = self.cleaned_data.get('allergies', '')
        if commit:
            instance.save()
        return instance
