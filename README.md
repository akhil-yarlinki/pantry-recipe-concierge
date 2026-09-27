# Smart Pantry & Recipe Concierge 🍳

An intelligent, multi-tool culinary AI assistant powered by Google Agent Development Kit (ADK), Gemini 2.5 Flash, and Vertex AI services.

![Smart Pantry & Recipe Concierge Demo](demo.gif)

---

## 🌟 Implemented Features & Integrations

All capabilities listed below are fully implemented and wired up in the [`app/`](app/) directory:

### 🧠 Cross-Session Memory (Vertex AI Memory Bank)
* Integrated with **Vertex AI Memory Bank** (`VertexAiMemoryBankService`) to automatically extract user dietary restrictions, favorite cuisines, and family preferences across chat turns (`generate_memories_callback`).
* Uses `PreloadMemoryTool` to inject remembered context into new sessions.

### 📦 Persistent Pantry Inventory (Google Cloud Firestore)
* Real-time CRUD operations against **Cloud Firestore** for managing pantry ingredients:
  * `add_pantry_item`: Add or update ingredient quantities, categories, and expiration dates.
  * `get_pantry_items`: Retrieve stored pantry inventory.
  * `delete_pantry_item`: Remove used or expired ingredients.

### 🔍 Recipe Search & Favorite Bookmarking
* `search_online_recipes`: Queries TheMealDB API to find real meal recipes based on ingredients available in the user's pantry.
* `save_favorite_recipe` & `get_favorite_recipes`: Bookmarks and retrieves user-saved favorite recipes in Firestore.

### 📊 Recipe Scaling & Macro Calculations
* `scale_recipe_and_calculate_macros`: Recalculates ingredient quantities for custom target servings (e.g., scaling from 4 to 6 servings) and estimates total calories and per-serving macronutrient breakdowns.
* Uses **Agent Engine Sandbox Code Executor** (`AgentEngineSandboxCodeExecutor`) for secure Python calculations.

### 📍 Grocery & Location Services (Google Maps & Places)
* `geocode_address`: Geocodes physical street addresses using the Google Maps Geocoding API.
* `find_nearby_places`: Finds nearby supermarkets, specialty Asian/Indian grocers, and farmers' markets using the Google Places API (New).

### 🖼️ AI Dish Image Generation (Vertex AI Imagen 3)
* `generate_dish_image`: Generates high-definition AI dish previews using `gemini-3.1-flash-lite-image` in the `global` region.
* Saves generated images as Playground artifacts (`tool_context.save_artifact`) and uploads them to a public **Google Cloud Storage** bucket (`pantry-recipe-concierge-assets-5119`).

### 🎥 AI Dish Video Generation (Vertex AI Omni Model)
* `generate_dish_video`: Generates short culinary videos using Google's Omni model (`gemini-omni-flash-preview`) in the `global` region via the Vertex AI Interactions API.
* Saves generated video artifacts (`tool_context.save_artifact`) and uploads raw video bytes directly to public Cloud Storage (`pantry-recipe-concierge-assets-5119`).

### 💻 Web Chat Interface
* Minimal FastAPI proxy server paired with a custom responsive web frontend (`frontend/static/index.html`).
* Features an emerald culinary theme, category navigation bar, quick prompt pills, copy-to-clipboard buttons, animated loading indicators, and full-screen image lightboxes.

---

## 🔮 Planned / Future Features

The following features were outlined in initial design concepts but are **planned for future releases** and are not yet implemented in code:
* 📷 *Barcode & Receipt OCR Scanning*: Automated pantry addition from receipt photos or package barcodes.
* 🛒 *Automated Grocery Checkout*: Direct cart integration with online grocery delivery services.

---

## 🛠️ Local Setup & Running Instructions

### Prerequisites
* Python 3.11+
* [`uv`](https://docs.astral.sh/uv/) package manager
* Google Cloud SDK with authenticated project credentials (`gcloud auth application-default login`)

### Installation

1. Install project dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

2. Set required environment variables:
   ```bash
   export GOOGLE_CLOUD_PROJECT="<your-gcp-project-id>"
   export AGENT_DIRECTORY="app"
   ```

3. Start the local frontend web server:
   ```bash
   cd frontend
   python main.py
   ```

4. Open your browser and navigate to the local host port output by the server (typically port `8080`).

---

## 📁 Repository Structure

```
pantry-recipe-concierge/
├── app/
│   ├── agent.py               # Root LlmAgent definition, Memory Bank, and tool registration
│   ├── tools.py               # Firestore, Search, Places, Imagen 3, and Omni video tools
│   └── fast_api_app.py        # ADK FastAPI application entrypoint
├── frontend/
│   ├── main.py                # FastAPI proxy server for web UI
│   └── static/
│       └── index.html         # Custom responsive chat UI
├── demo.gif                   # Looping demo recording
├── agents-cli-manifest.yaml   # Agent manifest configuration
└── pyproject.toml             # Python project dependencies
```
