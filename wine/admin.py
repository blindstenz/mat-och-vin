from django.contrib import admin

from .models import Pairing, RecipeProfile, WineStyle


@admin.register(WineStyle)
class WineStyleAdmin(admin.ModelAdmin):
    list_display = ["name", "colour", "body", "acidity", "tannin", "sweetness"]
    list_filter = ["colour"]
    search_fields = ["name", "grapes", "regions"]


@admin.register(RecipeProfile)
class RecipeProfileAdmin(admin.ModelAdmin):
    list_display = ["recipe", "main_component", "cooking_method", "sauce", "weight", "edited_by_user"]


@admin.register(Pairing)
class PairingAdmin(admin.ModelAdmin):
    list_display = ["recipe", "style", "rank", "source", "rating"]
    list_filter = ["source", "rating"]
