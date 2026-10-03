import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .models import Recipe, Tag
from .templatetags.recipe_extras import split_quantity

# 1x1 transparent GIF, enough for ImageField validation.
TINY_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00"
    b"\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


class RecipeModelTests(TestCase):
    def test_lines_skip_blanks_and_whitespace(self):
        recipe = Recipe(ingredients="400 g nötfärs\n\n  1 gul lök  \n", steps="Hacka.\nStek.")
        self.assertEqual(recipe.ingredient_list, ["400 g nötfärs", "1 gul lök"])
        self.assertEqual(recipe.step_list, ["Hacka.", "Stek."])

    def test_total_minutes(self):
        self.assertEqual(Recipe(prep_minutes=10, cook_minutes=20).total_minutes, 30)
        self.assertEqual(Recipe(cook_minutes=20).total_minutes, 20)
        self.assertIsNone(Recipe().total_minutes)


class SplitQuantityTests(SimpleTestCase):
    def test_amount_and_unit_are_split_off(self):
        self.assertEqual(split_quantity("1,5 kg lammstek"), ("1,5 kg", "lammstek"))
        self.assertEqual(split_quantity("2 kvistar rosmarin"), ("2 kvistar", "rosmarin"))
        self.assertEqual(split_quantity("½ tsk salt"), ("½ tsk", "salt"))
        self.assertEqual(split_quantity("2-3 st ägg"), ("2-3 st", "ägg"))

    def test_amount_without_unit(self):
        self.assertEqual(split_quantity("4 vitlöksklyftor"), ("4", "vitlöksklyftor"))
        self.assertEqual(split_quantity("4 gurkor"), ("4", "gurkor"))

    def test_line_without_amount_is_kept_whole(self):
        self.assertEqual(split_quantity("salt och peppar"), ("", "salt och peppar"))


class RecipeViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("bjorn", password="hemligt-lösen-123")
        self.other = User.objects.create_user("gäst", password="hemligt-lösen-123")
        self.client.force_login(self.user)

    def make(self, title, owner=None, **kwargs):
        return Recipe.objects.create(owner=owner or self.user, title=title, **kwargs)

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(reverse("recipes:list"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('recipes:list')}")

    def test_list_shows_only_own_recipes(self):
        self.make("Lammstek")
        self.make("Gästens pasta", owner=self.other)
        response = self.client.get(reverse("recipes:list"))
        self.assertContains(response, "Lammstek")
        self.assertNotContains(response, "Gästens pasta")

    def test_other_users_recipe_is_404(self):
        recipe = self.make("Hemligt", owner=self.other)
        for name in ("detail", "edit", "delete"):
            response = self.client.get(reverse(f"recipes:{name}", args=[recipe.pk]))
            self.assertEqual(response.status_code, 404, name)

    def test_search_matches_ingredients_and_tags(self):
        lamb = self.make("Lammstek", ingredients="1,5 kg lammstek\nrosmarin")
        pasta = self.make("Pasta")
        pasta.tags.add(Tag.objects.create(name="vardag"))
        self.make("Sallad")

        response = self.client.get(reverse("recipes:list"), {"q": "rosmarin"})
        self.assertEqual(list(response.context["recipes"]), [lamb])

        response = self.client.get(reverse("recipes:list"), {"q": "varda"})
        self.assertEqual(list(response.context["recipes"]), [pasta])

    def test_tag_filter(self):
        pasta = self.make("Pasta")
        pasta.tags.add(Tag.objects.create(name="vardag"))
        self.make("Sallad")
        response = self.client.get(reverse("recipes:list"), {"tagg": "vardag"})
        self.assertEqual(list(response.context["recipes"]), [pasta])

    def test_htmx_search_returns_partial(self):
        self.make("Lammstek")
        response = self.client.get(reverse("recipes:list"), {"q": "lamm"}, HTTP_HX_REQUEST="true")
        self.assertTemplateUsed(response, "recipes/_recipe_results.html")
        self.assertTemplateNotUsed(response, "base.html")
        self.assertContains(response, "Lammstek")

    def test_create_with_tags(self):
        response = self.client.post(
            reverse("recipes:create"),
            {
                "title": "Lammstek med rosmarin",
                "servings": 6,
                "ingredients": "1,5 kg lammstek\n2 kvistar rosmarin",
                "steps": "Sätt ugnen på 150 °C.\nStek.",
                "tag_names": "Lamm, helg, lamm, ",
            },
        )
        recipe = Recipe.objects.get()
        self.assertRedirects(response, recipe.get_absolute_url())
        self.assertEqual(recipe.owner, self.user)
        self.assertEqual(sorted(t.name for t in recipe.tags.all()), ["helg", "lamm"])

    def test_create_requires_title(self):
        response = self.client.post(reverse("recipes:create"), {"title": ""})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Recipe.objects.exists())

    def test_edit_updates_tags(self):
        recipe = self.make("Pasta")
        recipe.tags.add(Tag.objects.create(name="vardag"))
        response = self.client.post(
            reverse("recipes:edit", args=[recipe.pk]),
            {"title": "Pasta carbonara", "tag_names": "pasta"},
        )
        self.assertRedirects(response, recipe.get_absolute_url())
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, "Pasta carbonara")
        self.assertEqual([t.name for t in recipe.tags.all()], ["pasta"])

    def test_edit_form_prefills_tags(self):
        recipe = self.make("Pasta")
        recipe.tags.add(Tag.objects.create(name="vardag"), Tag.objects.create(name="pasta"))
        response = self.client.get(reverse("recipes:edit", args=[recipe.pk]))
        self.assertContains(response, 'value="pasta, vardag"')

    def test_delete_needs_post(self):
        recipe = self.make("Pasta")
        self.client.get(reverse("recipes:delete", args=[recipe.pk]))
        self.assertTrue(Recipe.objects.filter(pk=recipe.pk).exists())
        response = self.client.post(reverse("recipes:delete", args=[recipe.pk]))
        self.assertRedirects(response, reverse("recipes:list"))
        self.assertFalse(Recipe.objects.filter(pk=recipe.pk).exists())

    def test_detail_renders_lines(self):
        recipe = self.make("Lammstek", ingredients="lammstek\nvitlök", steps="Gnid in.\nStek.")
        response = self.client.get(recipe.get_absolute_url())
        self.assertContains(response, "<li>Gnid in.</li>", html=True)
        self.assertContains(response, "vitlök")
        self.assertContains(response, "Köksläge")


class RecipePhotoTests(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media)
        self.user = get_user_model().objects.create_user("bjorn")
        self.client.force_login(self.user)

    def test_upload_photo(self):
        with override_settings(MEDIA_ROOT=self.media):
            photo = SimpleUploadedFile("lamm.gif", TINY_GIF, content_type="image/gif")
            self.client.post(reverse("recipes:create"), {"title": "Lammstek", "photo": photo})
            recipe = Recipe.objects.get()
            self.assertTrue(recipe.photo.name.startswith("recipes/"))
            response = self.client.get(recipe.get_absolute_url())
            self.assertContains(response, recipe.photo.url)
