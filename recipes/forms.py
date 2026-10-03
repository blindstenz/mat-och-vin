from django import forms

from .models import Recipe, Tag


class RecipeForm(forms.ModelForm):
    tag_names = forms.CharField(
        label="Taggar",
        required=False,
        help_text="Kommaseparerade, t.ex. pasta, vardag, jul.",
    )

    class Meta:
        model = Recipe
        fields = [
            "title",
            "description",
            "servings",
            "prep_minutes",
            "cook_minutes",
            "ingredients",
            "steps",
            "notes",
            "source",
            "photo",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
            "ingredients": forms.Textarea(attrs={"rows": 8, "placeholder": "400 g nötfärs\n1 gul lök"}),
            "steps": forms.Textarea(attrs={"rows": 10}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["tag_names"].initial = ", ".join(t.name for t in self.instance.tags.all())

    def clean_tag_names(self):
        names = [n.strip().lower() for n in self.cleaned_data["tag_names"].split(",")]
        # Keep order, drop blanks and duplicates.
        return list(dict.fromkeys(n for n in names if n))

    def save(self, commit=True):
        recipe = super().save(commit=commit)
        if commit:
            self.save_tags(recipe)
        return recipe

    def save_tags(self, recipe):
        tags = [Tag.objects.get_or_create(name=name)[0] for name in self.cleaned_data["tag_names"]]
        recipe.tags.set(tags)
