from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from recipes.models import Recipe

from . import ai, service
from .forms import RecipeProfileForm
from .models import Pairing, RecipeProfile


def _recipe(request, pk):
    return get_object_or_404(Recipe, pk=pk, owner=request.user)


def _section(request, recipe, notice=""):
    context = {
        "recipe": recipe,
        "pairings": recipe.pairings.select_related("style"),
        "profile": RecipeProfile.objects.filter(recipe=recipe).first(),
        "claude_enabled": ai.is_configured(),
        "notice": notice,
    }
    return render(request, "wine/_wine_section.html", context)


@login_required
def wine_section(request, pk):
    return _section(request, _recipe(request, pk))


@login_required
@require_POST
def suggest(request, pk):
    recipe = _recipe(request, pk)
    _, notice = service.suggest(recipe, request.user)
    return _section(request, recipe, notice)


@login_required
def edit_profile(request, pk):
    recipe = _recipe(request, pk)
    instance = RecipeProfile.objects.filter(recipe=recipe).first() or RecipeProfile(recipe=recipe)
    form = RecipeProfileForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        prof = form.save(commit=False)
        prof.edited_by_user = True
        prof.save()
        service.suggest(recipe, request.user)
        return redirect(f"{recipe.get_absolute_url()}#vin")
    return render(request, "wine/profile_form.html", {"recipe": recipe, "form": form})


@login_required
@require_POST
def rate(request, pairing_id):
    pairing = get_object_or_404(Pairing, pk=pairing_id, recipe__owner=request.user)
    value = {"up": 1, "down": -1}.get(request.POST.get("value"), 0)
    # Clicking the same thumb again clears the rating.
    pairing.rating = 0 if pairing.rating == value else value
    pairing.save(update_fields=["rating"])
    if request.headers.get("HX-Request"):
        return render(request, "wine/_pairing.html", {"pairing": pairing})
    return redirect(f"{pairing.recipe.get_absolute_url()}#vin")
