from django.urls import path

from . import views

app_name = "wine"

urlpatterns = [
    path("recept/<int:pk>/", views.wine_section, name="section"),
    path("recept/<int:pk>/foresla/", views.suggest, name="suggest"),
    path("recept/<int:pk>/profil/", views.edit_profile, name="profile"),
    path("forslag/<int:pairing_id>/betyg/", views.rate, name="rate"),
]
