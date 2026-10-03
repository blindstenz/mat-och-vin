from django.db import models

from recipes.models import Recipe

from . import profile


class WineStyle(models.Model):
    class Colour(models.TextChoices):
        SPARKLING = "sparkling", "Mousserande"
        WHITE = "white", "Vitt"
        ROSE = "rose", "Rosé"
        RED = "red", "Rött"
        SWEET = "sweet", "Sött"
        FORTIFIED = "fortified", "Starkvin"

    key = models.SlugField("nyckel", max_length=50, unique=True)
    name = models.CharField("namn", max_length=100)
    colour = models.CharField("typ", max_length=10, choices=Colour.choices)
    body = models.PositiveSmallIntegerField("fyllighet (1-5)")
    acidity = models.PositiveSmallIntegerField("syra (1-5)")
    tannin = models.PositiveSmallIntegerField("strävhet (1-5)")
    sweetness = models.PositiveSmallIntegerField("sötma (1-5)")
    grapes = models.CharField("druvor", max_length=200, blank=True)
    regions = models.CharField("regioner", max_length=200, blank=True)
    pairs_with = models.CharField(
        "passar till", max_length=300, blank=True, help_text="Profilnycklar, mellanslagsseparerade."
    )

    class Meta:
        ordering = ["colour", "body", "name"]
        verbose_name = "vinstil"
        verbose_name_plural = "vinstilar"

    def __str__(self):
        return self.name

    @property
    def keywords(self):
        return set(self.pairs_with.split())


class RecipeProfile(models.Model):
    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE, related_name="wine_profile")
    main_component = models.CharField("huvudingrediens", max_length=20, choices=profile.MAIN_COMPONENTS)
    cooking_method = models.CharField(
        "tillagning", max_length=20, choices=profile.COOKING_METHODS, blank=True
    )
    sauce = models.CharField("sås", max_length=20, choices=profile.SAUCES, default="none")
    weight = models.CharField("tyngd", max_length=10, choices=profile.WEIGHTS, default="medium")
    flavours = models.JSONField("smaker", default=list, blank=True)
    edited_by_user = models.BooleanField("ändrad för hand", default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "receptprofil"
        verbose_name_plural = "receptprofiler"

    def __str__(self):
        return f"Profil för {self.recipe}"

    @property
    def keywords(self):
        keys = {self.main_component, self.cooking_method, self.sauce, *self.flavours}
        keys.discard("")
        keys.discard("none")
        return keys

    @property
    def flavour_labels(self):
        return [profile.LABELS.get(f, f) for f in self.flavours]


class Pairing(models.Model):
    class Source(models.TextChoices):
        RULES = "rules", "Regler"
        AI = "ai", "Claude"

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="pairings")
    style = models.ForeignKey(WineStyle, on_delete=models.CASCADE, related_name="pairings")
    rank = models.PositiveSmallIntegerField("ordning", default=1)
    score = models.FloatField("poäng", default=0)
    reason = models.TextField("varför", blank=True)
    source = models.CharField("källa", max_length=10, choices=Source.choices, default=Source.RULES)
    # +1 / -1 from the user, 0 = not rated.
    rating = models.SmallIntegerField("betyg", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["rank"]
        unique_together = [("recipe", "style")]
        verbose_name = "vinförslag"
        verbose_name_plural = "vinförslag"

    def __str__(self):
        return f"{self.style} till {self.recipe}"


def user_feedback(user, main_component, exclude_recipe=None):
    """Sum of the user's ratings per style for other dishes with the same main component."""
    rows = Pairing.objects.filter(
        recipe__owner=user,
        recipe__wine_profile__main_component=main_component,
    ).exclude(rating=0)
    if exclude_recipe is not None:
        rows = rows.exclude(recipe=exclude_recipe)
    rows = rows.values_list("style_id", "rating")
    feedback = {}
    for style_id, rating in rows:
        feedback[style_id] = feedback.get(style_id, 0) + rating
    return feedback

