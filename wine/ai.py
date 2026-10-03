"""Claude-backed steps of the wine suggestion.

1. profile_recipe(): read the recipe and fill in a RecipeProfile.
2. rank_with_claude(): pick and explain the best styles among the rules
   engine's candidates. Claude may only choose from that list, which keeps
   results consistent with the reference table.

Both calls use structured output so the answer is always valid JSON.
Without ANTHROPIC_API_KEY the app falls back to the rules engine alone.
"""

import json
import logging

from django.conf import settings

from . import profile as vocab

logger = logging.getLogger(__name__)


class ClaudeUnavailable(Exception):
    """Claude could not be reached or gave no usable answer; use the rules."""


def is_configured():
    return bool(settings.ANTHROPIC_API_KEY)


def _client():
    import anthropic

    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY, timeout=60, max_retries=2)


def _ask(system, prompt, schema, max_tokens=4000):
    import anthropic

    try:
        response = _client().beta.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_config={
                "effort": "low",
                "format": {"type": "json_schema", "schema": schema},
            },
            # On a rare safety decline, let the API retry on a fallback model.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.APIConnectionError as error:
        raise ClaudeUnavailable("Kunde inte nå Claude.") from error
    except anthropic.RateLimitError as error:
        raise ClaudeUnavailable("Claude är upptagen just nu, försök igen om en stund.") from error
    except anthropic.APIStatusError as error:
        logger.warning("Claude API error %s: %s", error.status_code, error.message)
        raise ClaudeUnavailable("Claude svarade med ett fel.") from error

    if response.stop_reason in ("refusal", "max_tokens"):
        raise ClaudeUnavailable(f"Claude gav inget svar ({response.stop_reason}).")
    text = next((block.text for block in response.content if block.type == "text"), None)
    if not text:
        raise ClaudeUnavailable("Claude gav inget svar.")
    return json.loads(text)


def _recipe_text(recipe):
    parts = [f"Titel: {recipe.title}"]
    if recipe.description:
        parts.append(f"Beskrivning: {recipe.description}")
    if recipe.ingredients:
        parts.append("Ingredienser:\n" + recipe.ingredients)
    if recipe.steps:
        parts.append("Gör så:\n" + recipe.steps)
    if recipe.notes:
        parts.append(f"Anteckningar: {recipe.notes}")
    return "\n\n".join(parts)


def _keys(choices):
    return [key for key, _ in choices]


PROFILE_SCHEMA = {
    "type": "object",
    "properties": {
        "main_component": {"type": "string", "enum": _keys(vocab.MAIN_COMPONENTS)},
        "cooking_method": {"type": "string", "enum": _keys(vocab.COOKING_METHODS)},
        "sauce": {"type": "string", "enum": _keys(vocab.SAUCES)},
        "weight": {"type": "string", "enum": _keys(vocab.WEIGHTS)},
        "flavours": {"type": "array", "items": {"type": "string", "enum": _keys(vocab.FLAVOURS)}},
    },
    "required": ["main_component", "cooking_method", "sauce", "weight", "flavours"],
    "additionalProperties": False,
}

PROFILE_SYSTEM = (
    "You are a sommelier helping a home cook. Classify the recipe by what matters for "
    "wine pairing: the component that dominates the plate (judge by the finished dish, "
    "not ingredient count), the main cooking method, the dominant sauce, the overall "
    "weight, and only the flavours that are clearly prominent (usually 0-3). The recipe "
    "is usually in Swedish."
)


def profile_recipe(recipe):
    return _ask(PROFILE_SYSTEM, _recipe_text(recipe), PROFILE_SCHEMA, max_tokens=2000)


RANK_SYSTEM = (
    "Du är en sommelier som hjälper en hemmakock i Sverige. Välj de tre vinstilar ur "
    "listan som passar receptet bäst och motivera varje val med en kort mening på "
    "svenska (högst 25 ord) som nämner vad i rätten vinet möter, t.ex. syra mot tomat "
    "eller strävhet mot grillat kött. Välj gärna olika typer om flera passar lika bra. "
    "Hitta inte på stilar utanför listan."
)


def rank_with_claude(recipe, prof, candidates, count=3):
    keys = [c.style.key for c in candidates]
    schema = {
        "type": "object",
        "properties": {
            "picks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "style": {"type": "string", "enum": keys},
                        "reason": {"type": "string"},
                    },
                    "required": ["style", "reason"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["picks"],
        "additionalProperties": False,
    }
    lines = [
        f"- {c.style.key}: {c.style.name} ({c.style.get_colour_display()}; druvor: {c.style.grapes}; "
        f"regioner: {c.style.regions}; regelpoäng {c.score:.1f})"
        for c in candidates
    ]
    flavours = ", ".join(prof.flavour_labels) or "inga särskilda"
    prompt = (
        f"{_recipe_text(recipe)}\n\n"
        f"Profil: {prof.get_main_component_display()}, {prof.get_cooking_method_display() or 'okänd tillagning'}, "
        f"sås: {prof.get_sauce_display()}, tyngd: {prof.get_weight_display()}, smaker: {flavours}.\n\n"
        f"Kandidater (från pairingregler, högst poäng först):\n" + "\n".join(lines) +
        f"\n\nVälj {count}."
    )
    data = _ask(RANK_SYSTEM, prompt, schema)

    by_key = {c.style.key: c for c in candidates}
    picks, seen = [], set()
    for pick in data["picks"]:
        if pick["style"] in by_key and pick["style"] not in seen:
            seen.add(pick["style"])
            picks.append((by_key[pick["style"]], pick["reason"].strip()))
    if not picks:
        raise ClaudeUnavailable("Claude valde inga vinstilar.")
    return picks[:count]

