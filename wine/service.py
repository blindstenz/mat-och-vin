"""Produce and store wine suggestions for a recipe."""

import logging

from django.db import transaction

from . import ai
from .models import Pairing, RecipeProfile
from .rules import rank_styles

logger = logging.getLogger(__name__)

SUGGESTION_COUNT = 3
CANDIDATE_COUNT = 8


def ensure_profile(recipe):
    """Return the recipe's profile, asking Claude to create it if missing.

    Returns None when there is no profile and Claude is not available; the
    page then asks the user to fill the profile in by hand.
    """
    existing = RecipeProfile.objects.filter(recipe=recipe).first()
    if existing:
        return existing
    if not ai.is_configured():
        return None
    data = ai.profile_recipe(recipe)
    return RecipeProfile.objects.create(recipe=recipe, **data)


def suggest(recipe, user):
    """Replace the recipe's suggestions. Returns (profile, notice)."""
    notice = ""
    try:
        prof = ensure_profile(recipe)
    except ai.ClaudeUnavailable as error:
        return None, str(error)
    if prof is None:
        return None, ""

    ranked = rank_styles(prof, user=user)
    picks = None
    if ai.is_configured():
        try:
            picks = ai.rank_with_claude(recipe, prof, ranked[:CANDIDATE_COUNT], SUGGESTION_COUNT)
            source = Pairing.Source.AI
        except ai.ClaudeUnavailable as error:
            logger.info("Falling back to rules for recipe %s: %s", recipe.pk, error)
            notice = f"{error} Förslagen nedan kommer från de inbyggda reglerna."
    if picks is None:
        picks = [(scored, scored.reason) for scored in ranked[:SUGGESTION_COUNT]]
        source = Pairing.Source.RULES

    with transaction.atomic():
        # Keep the user's ratings for styles that are suggested again.
        old_ratings = dict(recipe.pairings.values_list("style_id", "rating"))
        recipe.pairings.all().delete()
        for rank, (scored, reason) in enumerate(picks, start=1):
            Pairing.objects.create(
                recipe=recipe,
                style=scored.style,
                rank=rank,
                score=scored.score,
                reason=reason,
                source=source,
                rating=old_ratings.get(scored.style.pk, 0),
            )
    return prof, notice


def clear_stale(recipe):
    """The recipe changed: drop suggestions and any profile Claude made."""
    recipe.pairings.all().delete()
    RecipeProfile.objects.filter(recipe=recipe, edited_by_user=False).delete()
