# app/agents/service/genimi.py
"""
Gemini service integration.
"""
import os
from pydantic_ai.models.gemini import GeminiModel

def get_model(model_name: str) -> GeminiModel:
    """Get Gemini model with specified name."""
    return GeminiModel(model_name, api_key=os.getenv("GEMINI_API_KEY"))
