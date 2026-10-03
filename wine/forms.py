from django import forms

from . import profile
from .models import RecipeProfile


class RecipeProfileForm(forms.ModelForm):
    flavours = forms.MultipleChoiceField(
        label="Framträdande smaker",
        choices=profile.FLAVOURS,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = RecipeProfile
        fields = ["main_component", "cooking_method", "sauce", "weight", "flavours"]
