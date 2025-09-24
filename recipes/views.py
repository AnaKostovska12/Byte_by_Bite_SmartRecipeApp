
import requests
from django.shortcuts import render
from django.conf import settings
from django.conf import settings

API_KEY = settings.API_KEY

import os

# SPOONACULAR_KEY = os.environ.get("SPOONACULAR_KEY")
SPOONACULAR_KEY = settings.SPOONACULAR_KEY


def home(request):
    """Home page with ingredient selection."""
    return render(request, "recipes/home.html")


def tips(request):
    """Tips page with cooking/kitchen tips."""
    return render(request, "recipes/tips.html")


def recipe_detail(request, recipe_id):
    """Show detailed information about a specific recipe."""
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information?includeNutrition=true&apiKey={API_KEY}"
    response = requests.get(url)
    recipe = response.json() if response.status_code == 200 else None

    return render(request, "recipes/recipe_detail.html", {"recipe": recipe})


def get_recipes(request):
    """
    Handle recipe search, random recipe fetch, or custom recipes by ingredients.
    Supports sorting by popularity, calories, price, healthiness, and protein.
    """
    sort = request.GET.get("sort", "")
    query = request.GET.get("query", "")
    recipes = []
    ingredients = []
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "random":
            url = f"https://api.spoonacular.com/recipes/random?number=1&apiKey={API_KEY}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                recipes = data.get("recipes", [])
            else:
                ingredients = []
                return render(request, "recipes/home.html", {
    "error": f"❌ Error fetching random recipe: {response.status_code}"
                })

            
        elif action == "custom":
            ingredients = request.POST.getlist("ingredients")
            if not ingredients:
                return render(request, "recipes/home.html", {"error": "Please select at least one ingredient."})

            query = ",".join(ingredients)
            search_url = (
                f"https://api.spoonacular.com/recipes/findByIngredients"
                f"?ingredients={query}&number=20&ranking=1&ignorePantry=true&apiKey={API_KEY}"
            )
            search_response = requests.get(search_url)
            if search_response.status_code != 200:
                print("❌ Error fetching recipes:", search_response.status_code, search_response.text)
                return render(request, "recipes/home.html", {"error": "Failed to fetch recipes. Try again later."})

            raw_recipes = search_response.json()[:20]  # top 10 recipes
            recipes = []
            for r in raw_recipes:
                recipe_id = r["id"]
                info_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information?includeNutrition=true&apiKey={API_KEY}"
                info_response = requests.get(info_url)
                if info_response.status_code == 200:
                    recipes.append(info_response.json())
                else:
                    print(f"⚠️ Failed to fetch detailed info for recipe {recipe_id}: {info_response.status_code}")

        request.session["recipes"] = recipes
        request.session["ingredients"] = ingredients

        return render(
            request,
            "recipes/recipe_list.html",
            {"recipes": recipes, "ingredients": ingredients, "sort": sort},
        )

    elif request.method == "GET":
        if query:
            url = f"https://api.spoonacular.com/recipes/complexSearch?query={query}&number=12&addRecipeInformation=true&apiKey={API_KEY}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                recipes = data.get("results", [])
                if sort == "popularity":
                    recipes.sort(key=lambda r: r.get("spoonacularScore", 0), reverse=True)
                elif sort == "calories":
                    def get_calories(recipe):
                        nutrients = recipe.get("nutrition", {}).get("nutrients", [])
                        for n in nutrients:
                            if n["name"].lower() == "calories":
                                return n["amount"]
                        return float("inf")
                    recipes.sort(key=get_calories)
                elif sort == "price":
                    recipes.sort(key=lambda r: r.get("pricePerServing", float("inf")))
                elif sort == "healthiness":
                    recipes.sort(key=lambda r: r.get("healthScore", 0), reverse=True)
                elif sort == "protein":
                    def get_protein(recipe):
                        nutrients = recipe.get("nutrition", {}).get("nutrients", [])
                        for n in nutrients:
                            if n["name"].lower() == "protein":
                                return n["amount"]
                        return 0
                    recipes.sort(key=get_protein, reverse=True)

            else:
                print("❌ Error fetching search results:", response.status_code, response.text)

            return render(
                request,
                "recipes/recipe_list.html",
                {"recipes": recipes, "ingredients": [], "sort": sort, "query": query},
            )
        elif "recipes" in request.session:
            recipes = request.session.get("recipes", [])
            ingredients = request.session.get("ingredients", [])

            if sort == "popularity":
                recipes.sort(key=lambda r: r.get("spoonacularScore", 0), reverse=True)
            elif sort == "calories":
                def get_calories(recipe):
                    nutrients = recipe.get("nutrition", {}).get("nutrients", [])
                    for n in nutrients:
                        if n["name"].lower() == "calories":
                            return n["amount"]
                    return float("inf")
                recipes.sort(key=get_calories)
            elif sort == "price":
                recipes.sort(key=lambda r: r.get("pricePerServing", float("inf")))
            elif sort == "healthiness":
                recipes.sort(key=lambda r: r.get("healthScore", 0), reverse=True)
            elif sort == "protein":
                def get_protein(recipe):
                    nutrients = recipe.get("nutrition", {}).get("nutrients", [])
                    for n in nutrients:
                        if n["name"].lower() == "protein":
                            return n["amount"]
                    return 0
                recipes.sort(key=get_protein, reverse=True)

            return render(
                request,
                "recipes/recipe_list.html",
                {"recipes": recipes, "ingredients": ingredients, "sort": sort},
            )

    return render(request, "recipes/home.html")
