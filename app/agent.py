# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.tools import (
    add_pantry_item,
    delete_pantry_item,
    find_nearby_places,
    generate_dish_image,
    generate_dish_video,
    geocode_address,
    get_favorite_recipes,
    get_pantry_items,
    save_favorite_recipe,
    scale_recipe_and_calculate_macros,
    search_online_recipes,
)


def _get_agent_engine_resource_name() -> str | None:
    metadata_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "deployment_metadata.json"
    )
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, "r") as f:
                data = json.load(f)
                return data.get("agent_engine_resource_name") or data.get(
                    "remote_agent_runtime_id"
                )
        except Exception:
            pass
    return None


agent_engine_name = _get_agent_engine_resource_name()
MEMORY_BANK_ID = "3043161762904932352"

# Ensure ADK auto-config picks up Memory Bank on Agent Runtime deployment
os.environ["GOOGLE_CLOUD_AGENT_ENGINE_ID"] = MEMORY_BANK_ID

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_name
)


async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: after each turn, send the session to Memory Bank for extraction."""
    try:
        await callback_context.add_session_to_memory()
    except Exception as e:
        print(f"Memory Bank generation notice: {e}")
    return None


def memory_bank_service_builder():
    """Builds VertexAiMemoryBankService for Memory Bank cross-session persistence."""
    return VertexAiMemoryBankService(
        project="qwiklabs-gcp-02-5119abf4dcfa",
        location="us-central1",
        agent_engine_id=MEMORY_BANK_ID,
    )


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the Smart Pantry & Recipe Concierge, a helpful culinary AI assistant. "
        "You assist home cooks with managing their pantry inventory in Firestore, searching "
        "online recipe databases for real meal ideas by ingredient, saving/retrieving favorite recipes, "
        "scaling recipe ingredient quantities or computing macro totals, generating AI dish preview images and short culinary videos, "
        "executing Python calculations in a secure Agent Engine sandbox, remembering user dietary preferences and facts "
        "across sessions using Memory Bank, and geocoding locations or locating nearby grocery stores and markets."
    ),
    tools=[
        add_pantry_item,
        get_pantry_items,
        delete_pantry_item,
        save_favorite_recipe,
        get_favorite_recipes,
        scale_recipe_and_calculate_macros,
        search_online_recipes,
        geocode_address,
        find_nearby_places,
        generate_dish_image,
        generate_dish_video,
        PreloadMemoryTool(),
    ],
    code_executor=code_executor,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
