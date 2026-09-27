"""Seeding script to populate initial pantry items and favorite recipes into Firestore."""

from google.cloud import firestore

# Hardcode project ID as string for Firestore client.
# IMPORTANT: Do NOT read from google.auth.default() or GOOGLE_CLOUD_PROJECT
PROJECT_ID = "qwiklabs-gcp-02-5119abf4dcfa"

db = firestore.Client(project=PROJECT_ID)

INITIAL_PANTRY_ITEMS = [
    {
        "item_name": "Garlic",
        "quantity": "6",
        "category": "Produce",
        "unit": "cloves",
        "expiration_date": "2026-10-30",
    },
    {
        "item_name": "Olive Oil",
        "quantity": "1",
        "category": "Pantry",
        "unit": "bottle",
        "expiration_date": "2027-01-01",
    },
    {
        "item_name": "Spaghetti Pasta",
        "quantity": "500",
        "category": "Pantry",
        "unit": "grams",
        "expiration_date": "2027-06-15",
    },
    {
        "item_name": "Parmesan Cheese",
        "quantity": "200",
        "category": "Dairy",
        "unit": "grams",
        "expiration_date": "2026-11-10",
    },
    {
        "item_name": "Cherry Tomatoes",
        "quantity": "1",
        "category": "Produce",
        "unit": "pint",
        "expiration_date": "2026-10-05",
    },
    {
        "item_name": "Eggs",
        "quantity": "12",
        "category": "Dairy",
        "unit": "large",
        "expiration_date": "2026-10-20",
    },
]

INITIAL_FAVORITE_RECIPES = [
    {
        "title": "Garlic Butter Pasta",
        "ingredients": [
            "500g Spaghetti Pasta",
            "4 cloves Garlic, minced",
            "3 tbsp Olive Oil or Butter",
            "50g Parmesan Cheese, grated",
            "Salt and Black Pepper to taste",
        ],
        "instructions": (
            "1. Boil spaghetti in salted water until al dente.\n"
            "2. Heat olive oil/butter in a pan over medium heat, add minced garlic and saute for 1-2 mins until fragrant.\n"
            "3. Toss drained pasta with the garlic oil and freshly grated parmesan cheese.\n"
            "4. Season with salt and black pepper before serving."
        ),
        "prep_time_minutes": 15,
        "tags": ["Quick", "Italian", "Vegetarian", "Pantry-Friendly"],
        "is_favorite": True,
    },
    {
        "title": "Fresh Tomato & Basil Omelet",
        "ingredients": [
            "3 Eggs",
            "1/2 cup Cherry Tomatoes, halved",
            "1 tbsp Olive Oil",
            "Salt and Black Pepper",
        ],
        "instructions": (
            "1. Whisk eggs with salt and pepper.\n"
            "2. Heat olive oil in a non-stick skillet over medium-low heat.\n"
            "3. Pour in whisked eggs and add cherry tomatoes.\n"
            "4. Cook until set, fold in half, and serve hot."
        ),
        "prep_time_minutes": 10,
        "tags": ["Breakfast", "High-Protein", "Quick"],
        "is_favorite": True,
    },
]


def seed():
    print(f"Seeding Firestore database for project '{PROJECT_ID}'...")

    # Seed pantry items
    pantry_batch = db.batch()
    for item in INITIAL_PANTRY_ITEMS:
        doc_id = item["item_name"].lower().replace(" ", "_")
        doc_ref = db.collection("pantry_items").document(doc_id)
        data = {**item, "updated_at": firestore.SERVER_TIMESTAMP}
        pantry_batch.set(doc_ref, data, merge=True)
    pantry_batch.commit()
    print(f"Seeded {len(INITIAL_PANTRY_ITEMS)} pantry items.")

    # Seed favorite recipes
    recipe_batch = db.batch()
    for recipe in INITIAL_FAVORITE_RECIPES:
        doc_id = recipe["title"].lower().replace(" ", "_")
        doc_ref = db.collection("favorite_recipes").document(doc_id)
        data = {**recipe, "saved_at": firestore.SERVER_TIMESTAMP}
        recipe_batch.set(doc_ref, data, merge=True)
    recipe_batch.commit()
    print(f"Seeded {len(INITIAL_FAVORITE_RECIPES)} favorite recipes.")

    print("Firestore seeding completed successfully!")


if __name__ == "__main__":
    seed()
