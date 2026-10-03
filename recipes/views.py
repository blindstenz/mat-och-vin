from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import RecipeForm
from .models import Recipe, Tag


def _own_recipes(request):
    return Recipe.objects.filter(owner=request.user)


@login_required
def recipe_list(request):
    query = request.GET.get("q", "").strip()
    tag = request.GET.get("tagg", "").strip()

    recipes = _own_recipes(request).prefetch_related("tags")
    if query:
        recipes = recipes.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(ingredients__icontains=query)
            | Q(tags__name__icontains=query)
        ).distinct()
    if tag:
        recipes = recipes.filter(tags__name=tag)

    context = {
        "recipes": recipes,
        "query": query,
        "active_tag": tag,
        "tags": Tag.objects.filter(recipes__owner=request.user).distinct(),
    }
    # HTMX live search only swaps the result list.
    if request.headers.get("HX-Request"):
        return render(request, "recipes/_recipe_results.html", context)
    return render(request, "recipes/recipe_list.html", context)


@login_required
def recipe_detail(request, pk):
    recipe = get_object_or_404(_own_recipes(request).prefetch_related("tags"), pk=pk)
    return render(request, "recipes/recipe_detail.html", {"recipe": recipe})


@login_required
def recipe_create(request):
    form = RecipeForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        recipe = form.save(commit=False)
        recipe.owner = request.user
        recipe.save()
        form.save_tags(recipe)
        messages.success(request, f"”{recipe.title}” sparades.")
        return redirect(recipe)
    return render(request, "recipes/recipe_form.html", {"form": form})


@login_required
def recipe_edit(request, pk):
    recipe = get_object_or_404(_own_recipes(request), pk=pk)
    form = RecipeForm(request.POST or None, request.FILES or None, instance=recipe)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Ändringarna sparades.")
        return redirect(recipe)
    return render(request, "recipes/recipe_form.html", {"form": form, "recipe": recipe})


@login_required
def recipe_delete(request, pk):
    recipe = get_object_or_404(_own_recipes(request), pk=pk)
    if request.method == "POST":
        title = recipe.title
        recipe.delete()
        messages.success(request, f"”{title}” togs bort.")
        return redirect("recipes:list")
    return render(request, "recipes/recipe_confirm_delete.html", {"recipe": recipe})
