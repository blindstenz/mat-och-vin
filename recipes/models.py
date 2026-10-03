from django.conf import settings
from django.db import models
from django.urls import reverse


class Tag(models.Model):
    name = models.CharField("namn", max_length=50, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "tagg"
        verbose_name_plural = "taggar"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    class Visibility(models.TextChoices):
        PRIVATE = "private", "Privat"
        SHARED = "shared", "Delad"
        PUBLIC = "public", "Offentlig"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="ägare",
    )
    title = models.CharField("titel", max_length=200)
    description = models.TextField("beskrivning", blank=True)
    servings = models.PositiveSmallIntegerField("portioner", null=True, blank=True)
    prep_minutes = models.PositiveSmallIntegerField("förberedelse (min)", null=True, blank=True)
    cook_minutes = models.PositiveSmallIntegerField("tillagning (min)", null=True, blank=True)
    # One ingredient / step per line, matching the import template.
    ingredients = models.TextField("ingredienser", blank=True, help_text="En ingrediens per rad.")
    steps = models.TextField("gör så", blank=True, help_text="Ett steg per rad.")
    notes = models.TextField("anteckningar", blank=True)
    source = models.CharField("källa (bok/länk)", max_length=500, blank=True)
    photo = models.ImageField("bild", upload_to="recipes/%Y/%m/", blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="recipes", verbose_name="taggar")
    visibility = models.CharField(
        "synlighet", max_length=10, choices=Visibility.choices, default=Visibility.PRIVATE
    )
    created_at = models.DateTimeField("skapad", auto_now_add=True)
    updated_at = models.DateTimeField("ändrad", auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "recept"
        verbose_name_plural = "recept"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("recipes:detail", args=[self.pk])

    @staticmethod
    def _lines(text):
        return [line.strip() for line in text.splitlines() if line.strip()]

    @property
    def ingredient_list(self):
        return self._lines(self.ingredients)

    @property
    def step_list(self):
        return self._lines(self.steps)

    @property
    def total_minutes(self):
        parts = [m for m in (self.prep_minutes, self.cook_minutes) if m]
        return sum(parts) if parts else None
