"""Firestore backend tools for Smart Pantry & Recipe Concierge."""

import json
import os
import urllib.parse
import urllib.request
import uuid
import base64
from google import genai
from google.adk.tools import ToolContext
from google.cloud import firestore, storage
from google.genai import types

# Hardcode project ID as string for Firestore client.
# IMPORTANT: Do NOT read from google.auth.default() or GOOGLE_CLOUD_PROJECT
# as those return project number on Agent Platform which breaks Firestore.
PROJECT_ID = "qwiklabs-gcp-02-5119abf4dcfa"
BUCKET_NAME = "pantry-recipe-concierge-assets-5119"

db = firestore.Client(project=PROJECT_ID)


def add_pantry_item(
    item_name: str,
    quantity: str,
    category: str = "General",
    unit: str = "",
    expiration_date: str = "",
) -> str:
    """Adds or updates an ingredient item in the user's pantry inventory in Firestore.

    Args:
        item_name: Name of the ingredient (e.g. 'Garlic', 'Olive Oil', 'Eggs').
        quantity: Amount available (e.g. '3', '1/2', '500').
        category: Food category (e.g. 'Produce', 'Pantry', 'Dairy', 'Spices').
        unit: Unit of measurement (e.g. 'cloves', 'tbsp', 'grams', 'carton').
        expiration_date: Optional expiration date string (YYYY-MM-DD).

    Returns:
        Confirmation message string.
    """
    doc_id = item_name.lower().replace(" ", "_")
    doc_ref = db.collection("pantry_items").document(doc_id)
    item_data = {
        "item_name": item_name,
        "quantity": quantity,
        "category": category,
        "unit": unit,
        "expiration_date": expiration_date,
        "updated_at": firestore.SERVER_TIMESTAMP,
    }
    doc_ref.set(item_data, merge=True)
    return f"Successfully saved '{item_name}' ({quantity} {unit}) under category '{category}' in pantry."


def get_pantry_items(category: str = "") -> str:
    """Retrieves current pantry inventory items from Firestore.

    Args:
        category: Optional category filter (e.g. 'Produce', 'Dairy'). If empty, retrieves all items.

    Returns:
        JSON string containing the list of pantry items.
    """
    collection_ref = db.collection("pantry_items")
    if category:
        query = collection_ref.where("category", "==", category)
        docs = query.stream()
    else:
        docs = collection_ref.stream()

    items = []
    for doc in docs:
        data = doc.to_dict()
        if "updated_at" in data and data["updated_at"]:
            data["updated_at"] = str(data["updated_at"])
        data["id"] = doc.id
        items.append(data)

    if not items:
        return "No pantry items found."
    return json.dumps(items, indent=2)


def delete_pantry_item(item_name: str) -> str:
    """Removes an ingredient item from the user's pantry inventory in Firestore.

    Args:
        item_name: Name of the ingredient to remove (e.g. 'Garlic').

    Returns:
        Confirmation message string.
    """
    doc_id = item_name.lower().replace(" ", "_")
    doc_ref = db.collection("pantry_items").document(doc_id)
    if doc_ref.get().exists:
        doc_ref.delete()
        return f"Successfully removed '{item_name}' from pantry."
    return f"Item '{item_name}' was not found in pantry."


def save_favorite_recipe(
    title: str,
    ingredients: list[str],
    instructions: str,
    prep_time_minutes: int = 15,
    tags: list[str] = None,
) -> str:
    """Saves a recipe to the user's saved favorite recipes in Firestore.

    Args:
        title: Title of the recipe (e.g. 'Garlic Butter Pasta').
        ingredients: List of required ingredients with quantities.
        instructions: Step-by-step cooking instructions.
        prep_time_minutes: Total preparation and cooking time in minutes.
        tags: Optional tags (e.g. ['Quick', 'Italian', 'Vegetarian']).

    Returns:
        Confirmation message string.
    """
    if tags is None:
        tags = []
    doc_id = title.lower().replace(" ", "_")
    doc_ref = db.collection("favorite_recipes").document(doc_id)
    recipe_data = {
        "title": title,
        "ingredients": ingredients,
        "instructions": instructions,
        "prep_time_minutes": prep_time_minutes,
        "tags": tags,
        "is_favorite": True,
        "saved_at": firestore.SERVER_TIMESTAMP,
    }
    doc_ref.set(recipe_data, merge=True)
    return f"Successfully saved recipe '{title}' to favorite recipes."


def get_favorite_recipes() -> str:
    """Retrieves saved favorite recipes from Firestore.

    Returns:
        JSON string containing the list of favorite recipes.
    """
    docs = db.collection("favorite_recipes").stream()
    recipes = []
    for doc in docs:
        data = doc.to_dict()
        if "saved_at" in data and data["saved_at"]:
            data["saved_at"] = str(data["saved_at"])
        data["id"] = doc.id
        recipes.append(data)

    if not recipes:
        return "No favorite recipes found."
    return json.dumps(recipes, indent=2)


def scale_recipe_and_calculate_macros(
    base_servings: int,
    target_servings: int,
    ingredients: list[dict],
) -> str:
    """Scales ingredient quantities for a target serving size and estimates nutritional macros.

    Args:
        base_servings: The original number of servings the recipe makes (e.g. 2).
        target_servings: The desired number of servings to prepare (e.g. 4).
        ingredients: A list of dicts, each with 'name', 'quantity' (float/int), 'unit' (str),
                     and optional estimated 'calories' per unit quantity.
                     Example: [{"name": "Spaghetti", "quantity": 200, "unit": "g", "calories": 3.5}]

    Returns:
        A JSON string formatted with scaled ingredient amounts and macro estimates.
    """
    if base_servings <= 0:
        return "Error: base_servings must be greater than 0."

    scale_factor = target_servings / base_servings
    scaled_ingredients = []
    total_calories = 0.0

    for ing in ingredients:
        name = ing.get("name", "Unknown ingredient")
        base_qty = float(ing.get("quantity", 0))
        unit = ing.get("unit", "")
        cal_per_unit = float(ing.get("calories", 0))

        scaled_qty = round(base_qty * scale_factor, 2)
        scaled_cals = round(base_qty * cal_per_unit * scale_factor, 1)
        total_calories += scaled_cals

        scaled_ingredients.append(
            {
                "name": name,
                "scaled_quantity": scaled_qty,
                "unit": unit,
                "estimated_calories": scaled_cals,
            }
        )

    result = {
        "base_servings": base_servings,
        "target_servings": target_servings,
        "scale_factor": scale_factor,
        "scaled_ingredients": scaled_ingredients,
        "total_estimated_calories": round(total_calories, 1),
        "calories_per_serving": (
            round(total_calories / target_servings, 1) if target_servings > 0 else 0
        ),
    }
    return json.dumps(result, indent=2)


def search_online_recipes(query: str) -> str:
    """Searches a public recipe database (TheMealDB) for real recipe ideas by keyword or main ingredient.

    Args:
        query: Ingredient or recipe keyword (e.g. 'pasta', 'chicken', 'garlic').

    Returns:
        JSON string containing matching online recipes with titles, categories, origin, thumbnail image, and ID.
    """
    api_key = os.environ.get("MEALDB_API_KEY", "1")
    q_lower = query.strip().lower()

    if q_lower in ["indian", "indian recipes", "indian food", "indian cuisine"]:
        indian_keywords = ["dal", "paneer", "biryani", "handi", "tandoori"]
        all_meals = []
        for kw in indian_keywords:
            url = f"https://www.themealdb.com/api/json/v1/{api_key}/search.php?s={urllib.parse.quote(kw)}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "SmartPantryConcierge/1.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        for m in data.get("meals") or []:
                            if m.get("idMeal") not in [x.get("idMeal") for x in all_meals]:
                                all_meals.append(m)
            except Exception:
                pass
        meals = all_meals
    else:
        encoded_query = urllib.parse.quote(query.strip())
        url = f"https://www.themealdb.com/api/json/v1/{api_key}/search.php?s={encoded_query}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SmartPantryConcierge/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status != 200:
                    return f"Error: Received HTTP status {response.status} from recipe API."
                data = json.loads(response.read().decode("utf-8"))
            meals = data.get("meals")
            if not meals:
                filter_url = f"https://www.themealdb.com/api/json/v1/{api_key}/filter.php?i={encoded_query}"
                filter_req = urllib.request.Request(filter_url, headers={"User-Agent": "SmartPantryConcierge/1.0"})
                with urllib.request.urlopen(filter_req, timeout=5) as filter_resp:
                    filter_data = json.loads(filter_resp.read().decode("utf-8"))
                    meals = filter_data.get("meals")
        except Exception as e:
            return f"Failed to fetch online recipes: {str(e)}"

    if not meals:
        return f"No online recipes found matching '{query}'."

    results = []
    for meal in meals[:10]:
        results.append(
            {
                "id": meal.get("idMeal"),
                "title": meal.get("strMeal"),
                "category": meal.get("strCategory", "Main"),
                "area": meal.get("strArea", "International"),
                "image_url": meal.get("strMealThumb"),
                "instructions": (
                    meal.get("strInstructions", "")[:300] + "..."
                    if meal.get("strInstructions")
                    else ""
                ),
            }
        )
    return json.dumps(results, indent=2)


def _get_maps_api_key() -> str:
    key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not key:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                for line in f:
                    if line.startswith("GOOGLE_MAPS_API_KEY="):
                        key = line.strip().split("=", 1)[1].strip()
                        os.environ["GOOGLE_MAPS_API_KEY"] = key
                        break
    return key


def geocode_address(address: str) -> str:
    """Uses the Google Maps Geocoding API to turn a physical address into latitude and longitude coordinates.

    Args:
        address: The address string to geocode (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA').

    Returns:
        JSON string containing key fields: formatted address (name/address), location (lat, lng), and place_id.
    """
    api_key = _get_maps_api_key()
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not set."

    encoded_address = urllib.parse.quote(address.strip())
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "SmartPantryConcierge/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("status") != "OK" or not data.get("results"):
            return f"Geocoding failed for address '{address}': {data.get('status')}"

        result = data["results"][0]
        output = {
            "name": result.get("formatted_address"),
            "address": result.get("formatted_address"),
            "location": result.get("geometry", {}).get("location"),
            "place_id": result.get("place_id"),
        }
        return json.dumps(output, indent=2)
    except Exception as e:
        return f"Error calling Geocoding API: {str(e)}"


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "grocery_store",
    radius_meters: float = 5000.0,
) -> str:
    """Uses the Google Places API (New) searchNearby endpoint to find nearby places of a given type.

    Args:
        latitude: Center latitude coordinate.
        longitude: Center longitude coordinate.
        place_type: Type of place to search for (e.g. 'grocery_store', 'supermarket', 'restaurant').
        radius_meters: Search radius in meters (default 5000).

    Returns:
        JSON string listing nearby places with key fields: name, address, and location.
    """
    api_key = _get_maps_api_key()
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not set."

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }
    payload = {
        "includedTypes": [place_type],
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "radius": radius_meters,
            }
        },
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        places_raw = data.get("places", [])
        if not places_raw:
            return f"No nearby places of type '{place_type}' found within {radius_meters}m."

        results = []
        for place in places_raw[:5]:
            display_name = place.get("displayName", {})
            name_text = (
                display_name.get("text")
                if isinstance(display_name, dict)
                else str(display_name)
            )
            results.append(
                {
                    "name": name_text,
                    "address": place.get("formattedAddress"),
                    "location": place.get("location"),
                }
            )
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error calling Places API (New): {str(e)}"


def generate_dish_image(
    prompt: str,
    tool_context: ToolContext = None,
) -> str:
    """Generates an image for a culinary dish or pantry item using gemini-3.1-flash-lite-image in global region,
    saves it as an artifact in Playground, uploads it to Google Cloud Storage, and returns its public https URL.

    Args:
        prompt: Description of the dish or meal presentation to generate (e.g. 'A freshly baked Margherita pizza with basil leaves').
        tool_context: ToolContext injected automatically by ADK framework.

    Returns:
        Public HTTPS URL string (https://storage.googleapis.com/pantry-recipe-concierge-assets-5119/<object>).
    """
    try:
        genai_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )
        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
        )

        if not response.candidates or not response.candidates[0].content.parts:
            return "Error: No image content returned by gemini-3.1-flash-lite-image model."

        part = response.candidates[0].content.parts[0]
        if not part.inline_data or not part.inline_data.data:
            return "Error: Image generation output did not contain inline image bytes."

        img_bytes = part.inline_data.data
        mime_type = part.inline_data.mime_type or "image/jpeg"
        ext = "jpg" if "jpeg" in mime_type or "jpg" in mime_type else "png"

        unique_id = uuid.uuid4().hex[:8]
        filename = f"dish_{unique_id}.{ext}"

        # 1. Save with tool_context.save_artifact for Playground Artifacts panel
        if tool_context is not None:
            artifact_part = types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload image bytes to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(img_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return public_url
    except Exception as e:
        return f"Error generating dish image: {str(e)}"


def generate_dish_video(
    prompt: str,
    tool_context: ToolContext = None,
) -> str:
    """Generates a short video preview for a culinary dish or recipe preparation using gemini-omni-flash-preview in global region,
    saves it as an artifact in Playground, uploads it to Google Cloud Storage, and returns its public https URL.

    Args:
        prompt: Description of the dish or meal preparation to render in the video (e.g. 'A short video of sizzling garlic butter pasta cooking in a pan').
        tool_context: ToolContext injected automatically by ADK framework.

    Returns:
        Public HTTPS URL string (https://storage.googleapis.com/pantry-recipe-concierge-assets-5119/<object>).
    """
    try:
        genai_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )
        resp = genai_client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
            timeout=120,
        )

        if not resp or not getattr(resp, "output_video", None):
            return "Error: No video output returned by gemini-omni-flash-preview model."

        v_obj = resp.output_video
        raw_bytes = (
            getattr(v_obj, "video_bytes", None)
            or getattr(v_obj, "data", None)
            or (v_obj[0].data if isinstance(v_obj, list) else None)
        )
        if not raw_bytes:
            return "Error: Video output object did not contain video bytes."

        if isinstance(raw_bytes, str):
            video_bytes = base64.b64decode(raw_bytes)
        else:
            video_bytes = raw_bytes

        mime_type = getattr(v_obj, "mime_type", None) or "video/mp4"
        ext = "mp4"

        unique_id = uuid.uuid4().hex[:8]
        filename = f"video_{unique_id}.{ext}"

        # 1. Save with tool_context.save_artifact for Playground Artifacts panel
        if tool_context is not None:
            artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload video bytes to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return public_url
    except Exception as e:
        return f"Error generating dish video: {str(e)}"





