"""Rules engine: score every wine style against a recipe profile.

Classic pairing principles, kept deliberately simple and explainable:
match body to the dish's weight, reward styles known to suit the main
component, cooking method, sauce and flavours, and rule out clashes
(tannic reds with fish, dry wine with dessert). The user's own thumbs
up/down on similar dishes nudge the score.
"""

from dataclasses import dataclass, field

from . import profile as vocab
from .models import WineStyle, user_feedback


@dataclass
class ScoredStyle:
    style: WineStyle
    score: float
    notes: list = field(default_factory=list)

    @property
    def reason(self):
        return " ".join(self.notes) or "Ett allsidigt vin till rätten."


WEIGHT_PHRASES = {"light": "lätt", "medium": "medeltung", "heavy": "mäktig"}


def _label(key):
    return vocab.LABELS.get(key, key).lower()


def score_style(style, prof, feedback=None):
    result = ScoredStyle(style, 0.0)
    keys = style.keywords
    sweet_dish = prof.main_component in ("dessert", "chocolate")
    spicy = prof.sauce == "spicy" or "spicy" in prof.flavours
    acidic = prof.sauce in ("tomato", "citrus") or "citrus" in prof.flavours
    rich_sauce = prof.sauce in ("creamy", "butter")

    target_body = vocab.WEIGHT_TO_BODY[prof.weight]
    body_fit = 3 - abs(style.body - target_body)
    result.score += body_fit
    if body_fit >= 2.5:
        result.notes.append(f"Fylligheten passar en {WEIGHT_PHRASES[prof.weight]} rätt.")

    if prof.main_component in keys:
        result.score += 4
        result.notes.insert(0, f"Klassiskt till {_label(prof.main_component)}.")
    if prof.cooking_method and prof.cooking_method in keys:
        result.score += 1.5
    if prof.sauce != "none" and prof.sauce in keys:
        result.score += 2
        result.notes.append(f"Fungerar med såsen ({_label(prof.sauce)}).")
    matched = [f for f in prof.flavours if f in keys]
    result.score += 1.5 * len(matched)
    if matched:
        result.notes.append("Möter smakerna: " + ", ".join(_label(f) for f in matched) + ".")

    if sweet_dish:
        if style.sweetness < 4:
            result.score -= 10
        else:
            result.score += 3
            result.notes.append("Vinet behöver vara sötare än desserten.")
    elif style.sweetness >= 4 and prof.main_component != "cheese" and "blue_cheese" not in prof.flavours:
        result.score -= 8

    if prof.main_component in ("fish", "shellfish") and style.tannin >= 4:
        result.score -= 4
    if spicy:
        if style.tannin >= 4:
            result.score -= 2
        if 2 <= style.sweetness <= 3:
            result.score += 1
            result.notes.append("Lite sötma dämpar hettan.")
    if acidic:
        if style.acidity >= 4:
            result.score += 1
            result.notes.append("Syran klarar tomat och citrus.")
        elif style.acidity <= 2:
            result.score -= 1
    if rich_sauce and style.tannin >= 4:
        result.score -= 1

    if feedback:
        bonus = max(-4, min(4, 2 * feedback.get(style.pk, 0)))
        result.score += bonus
        if bonus > 0:
            result.notes.append("Du har gillat den här stilen till liknande rätter.")

    return result


def rank_styles(prof, user=None, styles=None):
    styles = list(styles if styles is not None else WineStyle.objects.all())
    feedback = None
    if user is not None:
        # The recipe's own ratings are kept on its pairings; only learn from other dishes.
        feedback = user_feedback(user, prof.main_component, exclude_recipe=prof.recipe_id)
    scored = [score_style(style, prof, feedback) for style in styles]
    return sorted(scored, key=lambda s: s.score, reverse=True)
