from django.urls import path

from . import views

app_name = "recipes"

urlpatterns = [
    path("", views.recipe_list, name="list"),
    path("nytt/", views.recipe_create, name="create"),
    path("<int:pk>/", views.recipe_detail, name="detail"),
    path("<int:pk>/andra/", views.recipe_edit, name="edit"),
    path("<int:pk>/ta-bort/", views.recipe_delete, name="delete"),
]
