# recipes/views.py
import os
import json
import uuid
import logging
from typing import Any, Dict
import requests
from requests.exceptions import RequestException

from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .forms import RecipeRequestForm
from .models import RecipeRequest, GeneratedRecipe

logger = logging.getLogger(__name__)

# --- Airia configuration ---
AIRIA_RECIPE_AGENT_ENDPOINT = os.environ.get("AIRIA_RECIPE_AGENT_ENDPOINT", "")
# AIRIA_API_KEY = os.environ.get("AIRIA_API_KEY", "")
AIRIA_API_KEY = os.environ.get("AIRIA_API_KEY", "")
AIRIA_USER_ID = os.environ.get("AIRIA_USER_ID", "")


def _ensure_guid_or_generate(candidate: str) -> str:
    """Ensure AIRIA_USER_ID is a valid GUID, generate one if missing or invalid."""
    if not candidate:
        return str(uuid.uuid4())
    try:
        u = uuid.UUID(candidate)
        return str(u)
    except Exception:
        logger.warning("AIRIA_USER_ID is not a valid GUID; generating a new UUID for this request.")
        return str(uuid.uuid4())


def _build_strict_prompt(cuisine: str, allergies: str, ingredients: str, previous_error: str = "") -> str:
    """
    Build a strict instruction for Chef SafePlate agent to force JSON-only output.
    """
    instruction = (
        "INSTRUCTION: You are ONLY a recipe-generation model with allergy check. "
        "DO NOT introduce yourself or output any explanations or greetings.\n\n"
        "OUTPUT ONLY a single JSON object with EXACTLY FOUR keys: is_safe, safety_notes, recipe_name, recipe_text.\n\n"
        f"User inputs:\n"
        f"cuisine: {cuisine}\n"
        f"allergies: {allergies}\n"
        f"ingredients: {ingredients}\n"
    )
    if previous_error:
        instruction += f"previous_error: {previous_error}\n"
    instruction += (
        "\n"
        "Return one valid JSON object ONLY, with ALL FOUR keys, exactly like this structure:\n"
        "{\n"
        '  "is_safe": true,\n'
        '  "safety_notes": "Recipe is safe for specified allergies. Precautions: ...",\n'
        '  "recipe_name": "Your Recipe Title",\n'
        '  "recipe_text": "Ingredients:\\n- ingredient 1\\n- ingredient 2\\n\\nInstructions:\\n1. Step one\\n2. Step two"\n'
        "}\n\n"
        "CRITICAL: You MUST include all four keys (is_safe, safety_notes, recipe_name, recipe_text) in your response.\n"
        "Do not output ONLY recipe_name and recipe_text. All four keys are required."
    )
    return instruction


def call_recipe_agent(cuisine: str, allergies: str, ingredients: str, previous_error: str = "") -> Dict[str, Any]:
    """
    Call Airia pipeline and return JSON output from the agent.
    """
    if not AIRIA_API_KEY:
        return {"error": "AIRIA_API_KEY not set in environment."}

    user_input_str = _build_strict_prompt(cuisine, allergies, ingredients, previous_error)

    payload = {
        "userId": _ensure_guid_or_generate(AIRIA_USER_ID),
        "userInput": user_input_str,
        "asyncOutput": False
    }

    headers = {
        "X-API-KEY": AIRIA_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(AIRIA_RECIPE_AGENT_ENDPOINT, headers=headers, json=payload, timeout=60)
        print("\nThis is the payload")
        print(payload)
        resp.raise_for_status()
        api_data = resp.json()
        return api_data
    except RequestException as e:
        logger.exception("Airia request failed: %s", e)
        return {"error": str(e)}
    except ValueError:
        return {"error": "Failed to decode Airia JSON response", "raw_text": resp.text}


def parse_agent_output(agent_result: dict) -> dict:
    """
    Normalize the output from the Airia agent into consistent keys:
    recipe_name, recipe_text, is_safe, safety_notes.
    """
    recipe_name = "Untitled Recipe"
    recipe_text = "No recipe text provided."
    is_safe = False  # Default to False for safety
    safety_notes = "Failed to parse agent output properly."

    if not isinstance(agent_result, dict):
        print("NOT DICT INSTANCE")
        return {
            "recipe_name": recipe_name, 
            "recipe_text": recipe_text, 
            "is_safe": False,
            "safety_notes": f"Invalid agent output type: {type(agent_result)}"
        }

    # Check for "result" key first (new Airia response format)
    if "result" in agent_result:
        result_data = agent_result["result"]
        if isinstance(result_data, str):
            try:
                output = json.loads(result_data)
            except json.JSONDecodeError as e:
                return {
                    "recipe_name": recipe_name, 
                    "recipe_text": recipe_text, 
                    "is_safe": False,
                    "safety_notes": f"Failed to parse JSON from result string: {e}"
                }
        else:
            output = result_data
    else:
        # Fallback: Some Airia responses may wrap JSON in an "output" string
        output = agent_result.get("output", agent_result)

        if isinstance(output, str):
            s = output.strip()
            first = s.find("{")
            last = s.rfind("}")
            if first != -1 and last != -1 and last > first:
                try:
                    output = json.loads(s[first:last+1])
                except json.JSONDecodeError as e:
                    return {
                        "recipe_name": recipe_name, 
                        "recipe_text": recipe_text, 
                        "is_safe": False,
                        "safety_notes": f"Failed to parse JSON from agent string. Error: {e}. Content preview: {s[:200]}"
                    }
            else:
                return {
                    "recipe_name": recipe_name, 
                    "recipe_text": recipe_text, 
                    "is_safe": False,
                    "safety_notes": f"No JSON object found in agent output. Content preview: {s[:200]}"
                }

    # Parse the output dictionary and extract all four keys
    if isinstance(output, dict):
        recipe_name = output.get("recipe_name") or output.get("title") or recipe_name
        recipe_text = output.get("recipe_text") or output.get("text") or recipe_text
        
        # Parse is_safe - handle both boolean and string representations
        is_safe_raw = output.get("is_safe")
        if isinstance(is_safe_raw, bool):
            is_safe = is_safe_raw
        elif isinstance(is_safe_raw, str):
            is_safe = is_safe_raw.lower() in ["true", "yes", "1"]
        else:
            is_safe = False  # Default to False if not provided or invalid
        
        # Parse safety_notes - ensure it's a string
        safety_notes_raw = output.get("safety_notes")
        if isinstance(safety_notes_raw, str):
            safety_notes = safety_notes_raw
        elif safety_notes_raw is not None:
            safety_notes = str(safety_notes_raw)
        else:
            # If safety_notes is missing, provide a default based on is_safe
            if is_safe:
                safety_notes = "No safety notes provided. Please verify ingredients for allergen safety."
            else:
                safety_notes = "Recipe marked as unsafe but no safety notes provided."
        
        # Validate that we got all expected keys
        missing_keys = []
        if "recipe_name" not in output and "title" not in output:
            missing_keys.append("recipe_name")
        if "recipe_text" not in output and "text" not in output:
            missing_keys.append("recipe_text")
        if "is_safe" not in output:
            missing_keys.append("is_safe")
        if "safety_notes" not in output:
            missing_keys.append("safety_notes")
        
        if missing_keys:
            print(f"WARNING: Missing keys in agent output: {', '.join(missing_keys)}")
            print(f"Available keys: {list(output.keys())}")
            # Append warning to safety_notes
            if missing_keys:
                safety_notes += f" [WARNING: Response missing keys: {', '.join(missing_keys)}]"
    else:
        return {
            "recipe_name": recipe_name, 
            "recipe_text": recipe_text, 
            "is_safe": False,
            "safety_notes": f"Parsed output is not a dictionary. Type: {type(output)}"
        }

    return {
        "recipe_name": recipe_name, 
        "recipe_text": recipe_text, 
        "is_safe": is_safe, 
        "safety_notes": safety_notes
    }


@require_http_methods(["GET", "POST"])
def generate_safe_recipe(request):
    """
    Main view: handles GET (form) and POST (call agent + save recipe + render).
    """
    result = None
    form = RecipeRequestForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        print("\n=== FORM DEBUG ===")
        print("Cleaned data:", form.cleaned_data)
        recipe_request: RecipeRequest = form.save()
        print("Saved cuisine:", recipe_request.cuisine)
        print("Saved allergies:", recipe_request.allergies)
        print("Saved ingredients:", recipe_request.ingredients)
        
        cuisine = recipe_request.cuisine
        allergies = recipe_request.allergies
        ingredients = recipe_request.ingredients

        # Call Airia agent
        agent_result = call_recipe_agent(cuisine, allergies, ingredients)
        print("\nThis is agent result")
        print(agent_result)

        # Parse output safely
        parsed_result = parse_agent_output(agent_result)
        print("\nThis is the final parsed result")
        print(parsed_result)

        # Save GeneratedRecipe
        generated_recipe = GeneratedRecipe.objects.create(
            request=recipe_request,
            recipe_name=parsed_result["recipe_name"],
            recipe_text=parsed_result["recipe_text"],
            is_safe=parsed_result["is_safe"],
            safety_notes=parsed_result["safety_notes"]
        )

        all_attempts_qs = recipe_request.generated_recipes.all().order_by("created_at")
        result = {
            "recipe_name": generated_recipe.recipe_name,
            "recipe_text": generated_recipe.recipe_text,
            "is_safe": generated_recipe.is_safe,
            "safety_notes": generated_recipe.safety_notes,
            "all_attempts": all_attempts_qs
        }

    return render(request, "recipes/recipe_page.html", {"form": form, "result": result})
