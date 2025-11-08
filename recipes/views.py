from django.shortcuts import render
from .forms import RecipeRequestForm
from .models import RecipeRequest, GeneratedRecipe


def _simulate_chef_agent(cuisine, allergies, ingredients, attempt=1):
    """
    Simulates a chef agent that generates recipes.
    On first attempt, intentionally generates unsafe 'Pesto' recipe if 'nuts' allergy is present.
    On subsequent attempts, generates a safe alternative.
    All parameters are optional filters - blank values mean no filter applied.
    """
    allergies_list = [a.strip().lower() for a in allergies.split(',') if a.strip()]
    
    # First attempt: Generate unsafe Pesto if nuts allergy exists
    if attempt == 1 and 'nuts' in allergies_list:
        return {
            'recipe_name': 'Pesto Pasta',
            'recipe_text': 'Cook pasta. Make pesto with fresh basil, pine nuts, parmesan, garlic, and olive oil. Toss pasta with pesto and serve.',
        }
    
    # Safe alternative or normal recipe
    ingredients_list = [i.strip() for i in ingredients.split(',') if i.strip()]
    ingredients_str = ', '.join(ingredients_list[:3]) if ingredients_list else 'seasonal vegetables'
    
    # Handle blank cuisine
    cuisine_name = cuisine.strip() if cuisine else 'delicious'
    cuisine_text = f'{cuisine_name} ' if cuisine else ''
    
    return {
        'recipe_name': f'Safe {cuisine_name} Delight' if cuisine else 'Safe Delight',
        'recipe_text': f'A delicious {cuisine_text}recipe using {ingredients_str}. This recipe is carefully crafted to avoid all allergens{" including: " + allergies if allergies else ""}. Cook with care and enjoy!',
    }


def _simulate_inspector_agent(recipe_name, recipe_text, allergies):
    """
    Simulates an inspector agent that checks recipe safety.
    Fails any recipe containing 'Pesto' if 'nuts' allergy is present.
    If allergies is blank, always passes as safe (no filters to check).
    """
    # If no allergies specified, recipe is safe by default
    if not allergies or not allergies.strip():
        return {
            'is_safe': True,
            'safety_notes': 'Recipe has been verified safe (no allergy restrictions specified).',
        }
    
    allergies_list = [a.strip().lower() for a in allergies.split(',') if a.strip()]
    
    # Check if recipe contains allergens
    if 'nuts' in allergies_list and 'pesto' in recipe_name.lower():
        return {
            'is_safe': False,
            'safety_notes': 'UNSAFE: Recipe contains pesto which typically includes pine nuts. This violates the nuts allergy restriction.',
        }
    
    # Additional check for pine nuts in recipe text
    if 'nuts' in allergies_list and 'pine nuts' in recipe_text.lower():
        return {
            'is_safe': False,
            'safety_notes': 'UNSAFE: Recipe explicitly mentions pine nuts which are prohibited due to nut allergy.',
        }
    
    return {
        'is_safe': True,
        'safety_notes': 'Recipe has been verified safe for all specified allergies.',
    }


def generate_safe_recipe(request):
    """
    Main view for generating safe recipes.
    Handles form submission, calls chef agent, then inspector agent.
    Retries chef agent if recipe is deemed unsafe.
    """
    result = None
    form = RecipeRequestForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        # Save the request
        recipe_request = form.save()
        
        # Extract data
        cuisine = recipe_request.cuisine
        allergies = recipe_request.allergies
        ingredients = recipe_request.ingredients
        
        # First attempt with chef agent
        chef_result = _simulate_chef_agent(cuisine, allergies, ingredients, attempt=1)
        recipe_name = chef_result['recipe_name']
        recipe_text = chef_result['recipe_text']
        
        # Check with inspector agent
        inspection_result = _simulate_inspector_agent(recipe_name, recipe_text, allergies)
        
        # If unsafe, retry with chef agent
        if not inspection_result['is_safe']:
            # Save the unsafe attempt
            GeneratedRecipe.objects.create(
                request=recipe_request,
                recipe_name=recipe_name,
                recipe_text=recipe_text,
                is_safe=False,
                safety_notes=inspection_result['safety_notes']
            )
            
            # Retry with chef agent (attempt 2)
            chef_result = _simulate_chef_agent(cuisine, allergies, ingredients, attempt=2)
            recipe_name = chef_result['recipe_name']
            recipe_text = chef_result['recipe_text']
            
            # Re-check with inspector
            inspection_result = _simulate_inspector_agent(recipe_name, recipe_text, allergies)
        
        # Save the final recipe
        generated_recipe = GeneratedRecipe.objects.create(
            request=recipe_request,
            recipe_name=recipe_name,
            recipe_text=recipe_text,
            is_safe=inspection_result['is_safe'],
            safety_notes=inspection_result['safety_notes']
        )
        
        result = {
            'recipe_name': generated_recipe.recipe_name,
            'recipe_text': generated_recipe.recipe_text,
            'is_safe': generated_recipe.is_safe,
            'safety_notes': generated_recipe.safety_notes,
            'all_attempts': recipe_request.generated_recipes.all()
        }
    
    return render(request, 'recipes/recipe_page.html', {
        'form': form,
        'result': result,
    })
