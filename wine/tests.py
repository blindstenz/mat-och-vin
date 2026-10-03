import json
from types import SimpleNamespace
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from recipes.models import Recipe

from . import ai, service
from .models import Pairing, RecipeProfile, WineStyle
from .profile import VOCABULARY
from .rules import rank_styles
from .styles_data import WINE_STYLES


def profile(**kwargs):
    defaults = dict(main_component="beef", cooking_method="", sauce="none", weight="medium", flavours=[])
    defaults.update(kwargs)
    return RecipeProfile(**defaults)


def top_keys(prof, n=3, **kwargs):
    return [s.style.key for s in rank_styles(prof, **kwargs)[:n]]


class StyleDataTests(TestCase):
    def test_styles_seeded_by_migration(self):
        self.assertEqual(WineStyle.objects.count(), len(WINE_STYLES))

    def test_pairs_with_uses_profile_vocabulary(self):
        for style in WINE_STYLES:
            unknown = set(style["pairs_with"].split()) - VOCABULARY
            self.assertFalse(unknown, f"{style['key']}: {unknown}")


class RulesTests(TestCase):
    def test_grilled_beef_gets_full_reds(self):
        keys = top_keys(profile(main_component="beef", cooking_method="grilled", weight="heavy"))
        for key in keys:
            self.assertEqual(WineStyle.objects.get(key=key).colour, "red")

    def test_light_fish_gets_crisp_whites_not_tannic_reds(self):
        ranked = rank_styles(profile(main_component="fish", cooking_method="steamed", sauce="butter", weight="light"))
        self.assertIn(ranked[0].style.colour, ("white", "sparkling"))
        tannic = [s for s in ranked[:5] if s.style.tannin >= 4]
        self.assertEqual(tannic, [])

    def test_dessert_only_gets_sweet_wine(self):
        for scored in rank_styles(profile(main_component="dessert", weight="medium"))[:2]:
            self.assertGreaterEqual(scored.style.sweetness, 4)

    def test_sweet_wine_not_suggested_for_main_course(self):
        for scored in rank_styles(profile(main_component="lamb", weight="heavy"))[:5]:
            self.assertLess(scored.style.sweetness, 4)

    def test_tomato_pasta_prefers_italian_acidity(self):
        keys = top_keys(profile(main_component="pasta", sauce="tomato"), n=2)
        self.assertEqual(set(keys), {"chianti", "barbera"})

    def test_reason_mentions_main_component(self):
        best = rank_styles(profile(main_component="lamb", weight="heavy"))[0]
        self.assertIn("lamm", best.reason)

    def test_feedback_moves_style_up(self):
        user = get_user_model().objects.create_user("bjorn")
        prof = profile(main_component="lamb", weight="heavy")
        before = top_keys(prof, n=40, user=user)
        liked = WineStyle.objects.get(key=before[6])

        other = Recipe.objects.create(owner=user, title="Lammfärsbiffar")
        RecipeProfile.objects.create(recipe=other, main_component="lamb", weight="heavy")
        Pairing.objects.create(recipe=other, style=liked, rating=1)

        after = top_keys(prof, n=40, user=user)
        self.assertLess(after.index(liked.key), before.index(liked.key))

    def test_feedback_ignores_the_recipe_itself(self):
        user = get_user_model().objects.create_user("bjorn")
        recipe = Recipe.objects.create(owner=user, title="Lammstek")
        prof = RecipeProfile.objects.create(recipe=recipe, main_component="lamb", weight="heavy")
        before = top_keys(prof, n=40, user=user)
        Pairing.objects.create(recipe=recipe, style=WineStyle.objects.get(key=before[6]), rating=1)
        self.assertEqual(top_keys(prof, n=40, user=user), before)


def fake_response(payload, stop_reason="end_turn"):
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[SimpleNamespace(type="text", text=json.dumps(payload))],
    )


class AiTests(TestCase):
    def setUp(self):
        self.recipe = Recipe(title="Lammstek", ingredients="lammstek\nrosmarin", steps="Stek.")

    @override_settings(ANTHROPIC_API_KEY="test-key", CLAUDE_MODEL="claude-opus-5-5")
    @mock.patch("wine.ai._client")
    def test_profile_recipe_sends_schema_and_parses(self, client):
        payload = {"main_component": "lamb", "cooking_method": "roasted", "sauce": "none",
                   "weight": "heavy", "flavours": ["herby"]}
        create = client.return_value.beta.messages.create
        create.return_value = fake_response(payload)

        self.assertEqual(ai.profile_recipe(self.recipe), payload)
        kwargs = create.call_args.kwargs
        self.assertEqual(kwargs["model"], "claude-opus-5-5")
        self.assertEqual(kwargs["output_config"]["format"]["type"], "json_schema")
        self.assertIn("lammstek", kwargs["messages"][0]["content"])

    @override_settings(ANTHROPIC_API_KEY="test-key")
    @mock.patch("wine.ai._client")
    def test_refusal_raises_unavailable(self, client):
        client.return_value.beta.messages.create.return_value = fake_response({}, stop_reason="refusal")
        with self.assertRaises(ai.ClaudeUnavailable):
            ai.profile_recipe(self.recipe)

    @override_settings(ANTHROPIC_API_KEY="test-key")
    @mock.patch("wine.ai._client")
    def test_rank_ignores_unknown_and_duplicate_styles(self, client):
        prof = profile(main_component="lamb", weight="heavy")
        candidates = rank_styles(prof)[:5]
        first, second = candidates[0].style.key, candidates[1].style.key
        client.return_value.beta.messages.create.return_value = fake_response({"picks": [
            {"style": second, "reason": " Bra. "},
            {"style": "made_up", "reason": "x"},
            {"style": second, "reason": "dubblett"},
            {"style": first, "reason": "Också bra."},
        ]})
        picks = ai.rank_with_claude(self.recipe, prof, candidates)
        self.assertEqual([(c.style.key, r) for c, r in picks], [(second, "Bra."), (first, "Också bra.")])


class ServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("bjorn")
        self.recipe = Recipe.objects.create(owner=self.user, title="Lammstek")

    @override_settings(ANTHROPIC_API_KEY="")
    def test_without_claude_or_profile_does_nothing(self):
        prof, notice = service.suggest(self.recipe, self.user)
        self.assertIsNone(prof)
        self.assertFalse(self.recipe.pairings.exists())

    @override_settings(ANTHROPIC_API_KEY="")
    def test_rules_only_with_manual_profile(self):
        RecipeProfile.objects.create(recipe=self.recipe, main_component="lamb", weight="heavy")
        service.suggest(self.recipe, self.user)
        pairings = list(self.recipe.pairings.all())
        self.assertEqual(len(pairings), 3)
        self.assertEqual([p.rank for p in pairings], [1, 2, 3])
        self.assertTrue(all(p.source == Pairing.Source.RULES and p.reason for p in pairings))

    @override_settings(ANTHROPIC_API_KEY="test-key")
    @mock.patch("wine.ai.rank_with_claude")
    @mock.patch("wine.ai.profile_recipe")
    def test_claude_path(self, profile_recipe, rank_with_claude):
        profile_recipe.return_value = {"main_component": "lamb", "cooking_method": "roasted",
                                       "sauce": "none", "weight": "heavy", "flavours": ["herby"]}
        rank_with_claude.side_effect = lambda recipe, prof, candidates, count: [
            (candidates[1], "Örterna möter Syrahns peppar.")
        ]
        prof, notice = service.suggest(self.recipe, self.user)
        self.assertEqual(prof.main_component, "lamb")
        self.assertEqual(notice, "")
        pairing = self.recipe.pairings.get()
        self.assertEqual(pairing.source, Pairing.Source.AI)
        self.assertEqual(pairing.reason, "Örterna möter Syrahns peppar.")

    @override_settings(ANTHROPIC_API_KEY="test-key")
    @mock.patch("wine.ai.rank_with_claude", side_effect=ai.ClaudeUnavailable("Kunde inte nå Claude."))
    def test_falls_back_to_rules_when_claude_fails(self, _):
        RecipeProfile.objects.create(recipe=self.recipe, main_component="lamb", weight="heavy")
        _, notice = service.suggest(self.recipe, self.user)
        self.assertIn("Kunde inte nå Claude.", notice)
        self.assertEqual(self.recipe.pairings.filter(source=Pairing.Source.RULES).count(), 3)

    @override_settings(ANTHROPIC_API_KEY="")
    def test_resuggest_keeps_ratings(self):
        RecipeProfile.objects.create(recipe=self.recipe, main_component="lamb", weight="heavy")
        service.suggest(self.recipe, self.user)
        first = self.recipe.pairings.first()
        first.rating = 1
        first.save()
        service.suggest(self.recipe, self.user)
        self.assertEqual(self.recipe.pairings.get(style=first.style).rating, 1)

    def test_clear_stale_keeps_hand_edited_profile(self):
        prof = RecipeProfile.objects.create(recipe=self.recipe, main_component="lamb", edited_by_user=True)
        Pairing.objects.create(recipe=self.recipe, style=WineStyle.objects.first())
        service.clear_stale(self.recipe)
        self.assertFalse(self.recipe.pairings.exists())
        self.assertTrue(RecipeProfile.objects.filter(pk=prof.pk).exists())


@override_settings(ANTHROPIC_API_KEY="")
class ViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("bjorn")
        self.other = User.objects.create_user("gäst")
        self.recipe = Recipe.objects.create(owner=self.user, title="Lammstek", ingredients="lammstek")
        self.client.force_login(self.user)

    def test_detail_asks_for_profile_without_claude(self):
        response = self.client.get(self.recipe.get_absolute_url())
        self.assertContains(response, "Beskriv rätten")
        self.assertContains(response, reverse("wine:profile", args=[self.recipe.pk]))

    @override_settings(ANTHROPIC_API_KEY="test-key")
    def test_detail_autoloads_suggestions_with_claude(self):
        response = self.client.get(self.recipe.get_absolute_url())
        self.assertContains(response, 'hx-trigger="load"')

    def test_profile_form_saves_and_suggests(self):
        response = self.client.post(
            reverse("wine:profile", args=[self.recipe.pk]),
            {"main_component": "lamb", "cooking_method": "roasted", "sauce": "none",
             "weight": "heavy", "flavours": ["herby", "peppery"]},
        )
        self.assertRedirects(response, f"{self.recipe.get_absolute_url()}#vin", fetch_redirect_response=False)
        prof = self.recipe.wine_profile
        self.assertTrue(prof.edited_by_user)
        self.assertEqual(prof.flavours, ["herby", "peppery"])
        self.assertEqual(self.recipe.pairings.count(), 3)

        page = self.client.get(self.recipe.get_absolute_url())
        self.assertContains(page, "Föreslå igen")
        self.assertContains(page, self.recipe.pairings.first().style.name)

    def test_suggest_returns_partial(self):
        RecipeProfile.objects.create(recipe=self.recipe, main_component="lamb", weight="heavy")
        response = self.client.post(reverse("wine:suggest", args=[self.recipe.pk]), HTTP_HX_REQUEST="true")
        self.assertTemplateUsed(response, "wine/_wine_section.html")
        self.assertTemplateNotUsed(response, "base.html")
        self.assertEqual(self.recipe.pairings.count(), 3)

    def test_suggest_requires_post(self):
        self.assertEqual(self.client.get(reverse("wine:suggest", args=[self.recipe.pk])).status_code, 405)

    def test_rate_toggles(self):
        pairing = Pairing.objects.create(recipe=self.recipe, style=WineStyle.objects.first())
        url = reverse("wine:rate", args=[pairing.pk])
        self.client.post(url, {"value": "up"}, HTTP_HX_REQUEST="true")
        pairing.refresh_from_db()
        self.assertEqual(pairing.rating, 1)
        self.client.post(url, {"value": "down"}, HTTP_HX_REQUEST="true")
        pairing.refresh_from_db()
        self.assertEqual(pairing.rating, -1)
        self.client.post(url, {"value": "down"}, HTTP_HX_REQUEST="true")
        pairing.refresh_from_db()
        self.assertEqual(pairing.rating, 0)

    def test_other_users_recipe_is_404(self):
        theirs = Recipe.objects.create(owner=self.other, title="Hemligt")
        pairing = Pairing.objects.create(recipe=theirs, style=WineStyle.objects.first())
        self.assertEqual(self.client.get(reverse("wine:profile", args=[theirs.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("wine:suggest", args=[theirs.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("wine:rate", args=[pairing.pk]), {"value": "up"}).status_code, 404)

    def test_editing_ingredients_clears_suggestions(self):
        Pairing.objects.create(recipe=self.recipe, style=WineStyle.objects.first())
        self.client.post(reverse("recipes:edit", args=[self.recipe.pk]),
                         {"title": "Lammstek", "ingredients": "lammstek\nvitlök"})
        self.assertFalse(self.recipe.pairings.exists())

    def test_editing_notes_keeps_suggestions(self):
        Pairing.objects.create(recipe=self.recipe, style=WineStyle.objects.first())
        self.client.post(reverse("recipes:edit", args=[self.recipe.pk]),
                         {"title": "Lammstek", "ingredients": "lammstek", "notes": "Gott!"})
        self.assertTrue(self.recipe.pairings.exists())
