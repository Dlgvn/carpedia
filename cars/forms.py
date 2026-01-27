from django import forms
from .models import Car


class CarSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by name or brand...',
            'class': 'form-control'
        })
    )


class CarFilterForm(forms.Form):
    brand = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    year_min = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Min year',
            'class': 'form-control'
        })
    )
    year_max = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Max year',
            'class': 'form-control'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        brands = Car.objects.values_list('brand', flat=True).distinct().order_by('brand')
        brand_choices = [('', 'All Brands')] + [(b, b) for b in brands]
        self.fields['brand'].choices = brand_choices
