from django.db import models


class RecipeRequest(models.Model):
    """Model to store recipe generation requests"""
    cuisine = models.CharField(max_length=100, blank=True, default='')
    allergies = models.TextField(help_text="Comma-separated list of allergies", blank=True, default='')
    ingredients = models.TextField(help_text="Comma-separated list of ingredients", blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        cuisine_text = self.cuisine if self.cuisine else "any cuisine"
        return f"Recipe Request for {cuisine_text}"


class GeneratedRecipe(models.Model):
    """Model to store generated recipes and their safety status"""
    request = models.ForeignKey(RecipeRequest, on_delete=models.CASCADE, related_name='generated_recipes')
    recipe_name = models.CharField(max_length=200)
    recipe_text = models.TextField()
    is_safe = models.BooleanField(default=False)
    safety_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipe_name} - {'Safe' if self.is_safe else 'Unsafe'}"
