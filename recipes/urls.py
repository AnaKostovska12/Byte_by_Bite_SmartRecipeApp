from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),               # Root URL shows form
    path('recipes/', views.get_recipes, name='get_recipes'),  # POST here to get recipes
    path('tips/', views.tips, name='tips'),
    path('recipe/<int:recipe_id>/', views.recipe_detail, name='recipe_detail'),
    
]