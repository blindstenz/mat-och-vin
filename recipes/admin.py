from django.contrib import admin

from .models import Recipe, Tag


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "visibility", "updated_at"]
    list_filter = ["visibility", "tags"]
    search_fields = ["title", "ingredients"]
    filter_horizontal = ["tags"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ["name"]
