from django.test import TestCase, Client
from django.urls import reverse
from .models import RecipeRequest, GeneratedRecipe
from .forms import RecipeRequestForm
from .views import _simulate_chef_agent, _simulate_inspector_agent

# TEST RECIPE INPUT FIELDS (user input)
class RecipeRequestModelTest(TestCase):
    # (a) Recipe fields successfully inputted
    def test_recipe_request_creation(self):
        request = RecipeRequest.objects.create(
            cuisine="Italian",
            allergies="nuts, dairy",
            ingredients="chicken, tomatoes, basil"
        )
        self.assertEqual(request.cuisine, "Italian")
        self.assertEqual(request.allergies, "nuts, dairy")
        self.assertEqual(request.ingredients, "chicken, tomatoes, basil")
        self.assertIsNotNone(request.created_at)
    
    # (b) Recipe fields stored as string
    def test_recipe_request_string_representation(self):
        request = RecipeRequest.objects.create(
            cuisine="Mexican",
            allergies="shellfish",
            ingredients="beef, peppers"
        )
        self.assertEqual(str(request), "Recipe Request for Mexican")
    
    # (c) Test blank fields are allowed
    def test_recipe_request_with_blank_fields(self):
        """Test that recipe requests can be created with blank fields"""
        request = RecipeRequest.objects.create(
            cuisine="",
            allergies="",
            ingredients=""
        )
        self.assertEqual(request.cuisine, "")
        self.assertEqual(request.allergies, "")
        self.assertEqual(request.ingredients, "")
        self.assertEqual(str(request), "Recipe Request for any cuisine")

# TEST RECIPE GENERATED FIELDS
class GeneratedRecipeModelTest(TestCase):    
    def setUp(self):
        self.request = RecipeRequest.objects.create(
            cuisine="Italian",
            allergies="nuts",
            ingredients="chicken, tomatoes"
        )
    # (a) Recipe generated successfully
    def test_generated_recipe_creation(self):
        recipe = GeneratedRecipe.objects.create(
            request=self.request,
            recipe_name="Test Recipe",
            recipe_text="Cook and serve.",
            is_safe=True,
            safety_notes="All good"
        )
        self.assertEqual(recipe.recipe_name, "Test Recipe")
        self.assertTrue(recipe.is_safe)
        self.assertEqual(recipe.request, self.request)
    
    # (b) Generated fields are stored as strings
    def test_generated_recipe_string_representation(self):
        recipe = GeneratedRecipe.objects.create(
            request=self.request,
            recipe_name="Safe Recipe",
            recipe_text="Instructions",
            is_safe=True
        )
        self.assertEqual(str(recipe), "Safe Recipe - Safe")
        
        unsafe_recipe = GeneratedRecipe.objects.create(
            request=self.request,
            recipe_name="Unsafe Recipe",
            recipe_text="Instructions",
            is_safe=False
        )
        self.assertEqual(str(unsafe_recipe), "Unsafe Recipe - Unsafe")
    
    # (c) Test that generated fields are relevant to initial input fields
    def test_recipe_request_relationship(self):
        recipe1 = GeneratedRecipe.objects.create(
            request=self.request,
            recipe_name="Attempt 1",
            recipe_text="First try",
            is_safe=False
        )
        recipe2 = GeneratedRecipe.objects.create(
            request=self.request,
            recipe_name="Attempt 2",
            recipe_text="Second try",
            is_safe=True
        )
        
        self.assertEqual(self.request.generated_recipes.count(), 2)
        self.assertIn(recipe1, self.request.generated_recipes.all())
        self.assertIn(recipe2, self.request.generated_recipes.all())

# TEST RECIPE REQUEST FORM
class RecipeRequestFormTest(TestCase):
    
    # (a) Valid data parsed successfully
    def test_form_valid_data(self):
        form_data = {
            'cuisine': 'Italian',
            'allergies': 'nuts, dairy',
            'ingredients': 'chicken, tomatoes, basil'
        }
        form = RecipeRequestForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    # (b) Form accepts blank cuisine (acts as no filter)
    def test_form_blank_cuisine(self):
        """Test form with blank cuisine is valid"""
        form_data = {
            'cuisine': '',
            'allergies': 'nuts',
            'ingredients': 'chicken'
        }
        form = RecipeRequestForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    # (c) Form accepts blank allergies (acts as no filter)
    def test_form_blank_allergies(self):
        """Test form with blank allergies is valid"""
        form_data = {
            'cuisine': 'Italian',
            'allergies': '',
            'ingredients': 'chicken'
        }
        form = RecipeRequestForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    # (d) Form accepts blank ingredients (acts as no filter)
    def test_form_blank_ingredients(self):
        """Test form with blank ingredients is valid"""
        form_data = {
            'cuisine': 'Italian',
            'allergies': 'nuts',
            'ingredients': ''
        }
        form = RecipeRequestForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    # (e) Form accepts all blank fields (no filters applied)
    def test_form_all_blank_fields(self):
        """Test form with all blank fields is valid"""
        form_data = {
            'cuisine': '',
            'allergies': '',
            'ingredients': ''
        }
        form = RecipeRequestForm(data=form_data)
        self.assertTrue(form.is_valid())


# TEST THAT AIRIA AGENT TWO CATCHES INCORRECT RECIPE (via _simulate_chef_agent)
class ChefAgentTest(TestCase):

    # (a) ensure that our hardcoded _simulate_chef_agent returns unsafe result
    def test_chef_generates_unsafe_pesto_on_first_attempt_with_nuts_allergy(self):
        result = _simulate_chef_agent(
            cuisine="Italian",
            allergies="nuts",
            ingredients="chicken, tomatoes",
            attempt=1
        )
        
        self.assertEqual(result['recipe_name'], 'Pesto Pasta')
        self.assertIn('pesto', result['recipe_text'].lower())
        self.assertIn('pine nuts', result['recipe_text'].lower())
    
    # (b) more robust version of the above
    def test_chef_generates_unsafe_pesto_with_multiple_allergies_including_nuts(self):
        result = _simulate_chef_agent(
            cuisine="Italian",
            allergies="dairy, nuts, shellfish",
            ingredients="pasta, basil",
            attempt=1
        )
        
        self.assertEqual(result['recipe_name'], 'Pesto Pasta')
        self.assertIn('pine nuts', result['recipe_text'].lower())
    
    # (c) check that agent #2 catches unsafe recipe output
    def test_chef_generates_safe_recipe_on_second_attempt(self):
        result = _simulate_chef_agent(
            cuisine="Italian",
            allergies="nuts",
            ingredients="chicken, tomatoes",
            attempt=2
        )
        
        self.assertNotEqual(result['recipe_name'], 'Pesto Pasta')
        self.assertIn('Safe', result['recipe_name'])
        self.assertIn('Italian', result['recipe_name'])
        self.assertNotIn('pine nuts', result['recipe_text'].lower())
    
    # (d) check that agent #2 generates safe correction
    def test_chef_generates_normal_recipe_without_nuts_allergy(self):
        result = _simulate_chef_agent(
            cuisine="Mexican",
            allergies="dairy",
            ingredients="beef, peppers",
            attempt=1
        )
        
        self.assertNotEqual(result['recipe_name'], 'Pesto Pasta')
        self.assertIn('Safe', result['recipe_name'])
        self.assertIn('Mexican', result['recipe_name'])
    
    # (e) check that new recipe conforms to old input filters
    def test_chef_uses_provided_ingredients(self):
        result = _simulate_chef_agent(
            cuisine="Chinese",
            allergies="shellfish",
            ingredients="tofu, broccoli, soy sauce",
            attempt=2
        )
        
        # Should mention some of the ingredients
        recipe_lower = result['recipe_text'].lower()
        self.assertTrue(
            'tofu' in recipe_lower or 
            'broccoli' in recipe_lower or 
            'soy sauce' in recipe_lower
        )
    
    # (f) check that blank cuisines have no effect
    def test_chef_handles_blank_cuisine(self):
        result = _simulate_chef_agent(
            cuisine="",
            allergies="dairy",
            ingredients="chicken, rice",
            attempt=1
        )
        
        self.assertIn('Safe', result['recipe_name'])
        self.assertIn('Delight', result['recipe_name'])
        # Should not cause errors
        self.assertIsNotNone(result['recipe_text'])
    
    # (g) check that blank allergies have no effect
    def test_chef_handles_blank_allergies(self):
        result = _simulate_chef_agent(
            cuisine="Italian",
            allergies="",
            ingredients="pasta, tomatoes",
            attempt=1
        )
        
        # Should NOT generate unsafe pesto if no allergies
        self.assertNotEqual(result['recipe_name'], 'Pesto Pasta')
        self.assertIn('Safe', result['recipe_name'])
    
    # (h) check that blank ingredients have no effect
    def test_chef_handles_blank_ingredients(self):
        result = _simulate_chef_agent(
            cuisine="Japanese",
            allergies="soy",
            ingredients="",
            attempt=1
        )
        
        self.assertIn('Safe', result['recipe_name'])
        # Should use default ingredients
        self.assertIn('seasonal vegetables', result['recipe_text'].lower())
    
    # (i) check that blank cuisines have no effect
    def test_chef_handles_all_blank_fields(self):
        result = _simulate_chef_agent(
            cuisine="",
            allergies="",
            ingredients="",
            attempt=1
        )
        
        self.assertIn('Safe', result['recipe_name'])
        self.assertIn('Delight', result['recipe_name'])
        self.assertIn('seasonal vegetables', result['recipe_text'].lower())


# TEST THAT AIRIA AGENT ONE RETURNS CORRECT FORMAT RECIPE (_simulate_inspector_agent)
class InspectorAgentTest(TestCase):  
    def test_inspector_catches_pesto_with_nuts_allergy(self):
        result = _simulate_inspector_agent(
            recipe_name="Pesto Pasta",
            recipe_text="Make pesto with basil and pine nuts",
            allergies="nuts"
        )
        
        self.assertFalse(result['is_safe'])
        self.assertIn('UNSAFE', result['safety_notes'])
        self.assertIn('pine nuts', result['safety_notes'].lower())
    
    # (a) pine nuts allergy corresponds to Agent #1 excluding pesto
    def test_inspector_catches_pine_nuts_in_recipe_text(self):
        result = _simulate_inspector_agent(
            recipe_name="Italian Pasta",
            recipe_text="Add pine nuts for extra flavor and texture",
            allergies="nuts"
        )
        
        self.assertFalse(result['is_safe'])
        self.assertIn('UNSAFE', result['safety_notes'])
        self.assertIn('pine nuts', result['safety_notes'].lower())
    
    # (b) inspector file approves recipe with no pine nuts
    def test_inspector_approves_safe_recipe(self):
        result = _simulate_inspector_agent(
            recipe_name="Tomato Basil Pasta",
            recipe_text="Cook pasta with fresh tomatoes and basil",
            allergies="nuts"
        )
        
        self.assertTrue(result['is_safe'])
        self.assertIn('safe', result['safety_notes'].lower())
    
    # (c) test response to multiple allergies
    def test_inspector_with_multiple_allergies(self):
        result = _simulate_inspector_agent(
            recipe_name="Pesto Pasta",
            recipe_text="Pesto with pine nuts",
            allergies="dairy, nuts, shellfish"
        )
        
        self.assertFalse(result['is_safe'])
    
    # (d) ensure that case-sensitivity has no impact
    def test_inspector_case_insensitive(self):
        result = _simulate_inspector_agent(
            recipe_name="PESTO PASTA",
            recipe_text="PINE NUTS",
            allergies="NUTS"
        )
        
        self.assertFalse(result['is_safe'])
    
    # (e) test no allergies
    def test_inspector_with_blank_allergies(self):
        result = _simulate_inspector_agent(
            recipe_name="Pesto Pasta",
            recipe_text="Make pesto with basil and pine nuts",
            allergies=""
        )
        
        # Should be safe because no allergy restrictions
        self.assertTrue(result['is_safe'])
        self.assertIn('no allergy restrictions', result['safety_notes'].lower())
    
    # (f) test agent #1 with whitespace (should be treated as blank)
    def test_inspector_with_whitespace_only_allergies(self):
        result = _simulate_inspector_agent(
            recipe_name="Pesto Pasta",
            recipe_text="Pine nuts included",
            allergies="   "
        )
        
        # Should be safe because effectively no allergies
        self.assertTrue(result['is_safe'])


# TEST FULL INTEGRATION (generate_safe_recipe)
class RecipeGenerationViewTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('recipes:generate_safe_recipe')
    
    # (a) GET request goes to recipe generation page
    def test_view_get_request(self):
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipes/recipe_page.html')
        self.assertIn('form', response.context)
        self.assertIsNone(response.context.get('result'))
    
    # (b) test unsafe AGENT #1 (hardcoded) and safe AGENT #2 (corrected)
    def test_full_workflow_unsafe_then_safe(self):
        """
        FULL PHASE 1 INTEGRATION TEST:
        - Submit form with nuts allergy
        - Chef generates unsafe Pesto (attempt 1)
        - Inspector catches it
        - Chef generates safe recipe (attempt 2)
        - Inspector approves it
        - Both attempts are saved and displayed
        """
        response = self.client.post(self.url, {
            'cuisine': 'Italian',
            'allergies': 'nuts',
            'ingredients': 'chicken, tomatoes, basil'
        })
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn('result', response.context)
        
        result = response.context['result']
        
        # Final recipe should be safe
        self.assertTrue(result['is_safe'])
        self.assertNotEqual(result['recipe_name'], 'Pesto Pasta')
        
        # Check database: should have 1 request and 2 generated recipes
        self.assertEqual(RecipeRequest.objects.count(), 1)
        self.assertEqual(GeneratedRecipe.objects.count(), 2)
        
        # Get the request and its attempts
        recipe_request = RecipeRequest.objects.first()
        attempts = recipe_request.generated_recipes.all().order_by('created_at')
        
        # First attempt should be unsafe Pesto
        first_attempt = attempts[0]
        self.assertEqual(first_attempt.recipe_name, 'Pesto Pasta')
        self.assertFalse(first_attempt.is_safe)
        self.assertIn('UNSAFE', first_attempt.safety_notes)
        
        # Second attempt should be safe
        second_attempt = attempts[1]
        self.assertTrue(second_attempt.is_safe)
        self.assertIn('Safe', second_attempt.recipe_name)
    
    # (c) test safe AGENT #1 (airia) and AGENT #2 response
    def test_workflow_safe_on_first_attempt(self):
        response = self.client.post(self.url, {
            'cuisine': 'Mexican',
            'allergies': 'dairy',
            'ingredients': 'beef, peppers, onions'
        })
        
        self.assertEqual(response.status_code, 200)
        result = response.context['result']
        
        # Should be safe
        self.assertTrue(result['is_safe'])
        
        # Should only have 1 generated recipe (no retry needed)
        self.assertEqual(GeneratedRecipe.objects.count(), 1)
    
    # (d) test form submission with all blank fields (should have no filters)
    def test_form_with_blank_fields(self):
        response = self.client.post(self.url, {
            'cuisine': '',
            'allergies': '',
            'ingredients': ''
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        # Form should be valid with blank fields
        self.assertTrue(response.context['form'].is_valid())
        # Should have a result
        self.assertIn('result', response.context)
        result = response.context['result']
        self.assertIsNotNone(result)
        # Recipe should be safe (no allergy filters)
        self.assertTrue(result['is_safe'])
    
    # (e) test that blank allergies mean no filters
    def test_workflow_with_blank_allergies(self):
        response = self.client.post(self.url, {
            'cuisine': 'Italian',
            'allergies': '',
            'ingredients': 'pasta, basil'
        })
        
        self.assertEqual(response.status_code, 200)
        result = response.context['result']
        
        # Should be safe on first attempt (no allergy restrictions)
        self.assertTrue(result['is_safe'])
        # Should only have 1 recipe (no retry needed)
        self.assertEqual(GeneratedRecipe.objects.count(), 1)
    
    # (f) test that context provided for all outputs
    def test_all_attempts_displayed(self):
        response = self.client.post(self.url, {
            'cuisine': 'Italian',
            'allergies': 'nuts',
            'ingredients': 'pasta, tomatoes'
        })
        
        result = response.context['result']
        all_attempts = result['all_attempts']
        
        # Should have 2 attempts (unsafe then safe)
        self.assertEqual(all_attempts.count(), 2)
        
        # Check they're in order
        attempts_list = list(all_attempts)
        self.assertFalse(attempts_list[0].is_safe)  # First is unsafe
        self.assertTrue(attempts_list[1].is_safe)   # Second is safe


# TEST EDGE CASES AND BOUNDARIES
class EdgeCaseTests(TestCase):
    
    # (a) empty allergy string
    def test_empty_allergy_string(self):
        result = _simulate_chef_agent(
            cuisine="Italian",
            allergies="",
            ingredients="pasta",
            attempt=1
        )
        # Should not trigger pesto since no nuts allergy
        self.assertNotEqual(result['recipe_name'], 'Pesto Pasta')
    
    # (b) whitespace in allergies
    def test_whitespace_only_allergies(self):
        result = _simulate_chef_agent(
            cuisine="Italian",
            allergies="  nuts  ,  dairy  ",
            ingredients="pasta",
            attempt=1
        )
        # Should still trigger pesto
        self.assertEqual(result['recipe_name'], 'Pesto Pasta')
    
    # (c) allergy case-sensitivity
    def test_mixed_case_allergies(self):
        result = _simulate_chef_agent(
            cuisine="Italian",
            allergies="NUTS, Dairy",
            ingredients="pasta",
            attempt=1
        )
        # Should trigger pesto regardless of case
        self.assertEqual(result['recipe_name'], 'Pesto Pasta')
    
    # (d) "nuts" in substring doesn't filter on nuts
    def test_nuts_substring_in_other_word(self):
        # 'coconuts' contains 'nuts' but might not be intended as tree nut allergy
        result = _simulate_chef_agent(
            cuisine="Thai",
            allergies="coconuts",  # Contains 'nuts' as substring
            ingredients="rice, vegetables",
            attempt=1
        )
        # Current implementation would trigger pesto - this documents the behavior
        # In real implementation, might want more sophisticated allergy parsing
