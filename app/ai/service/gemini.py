# app/agents/service/genimi.py
"""
Gemini service integration.
"""
import os
from pydantic_ai.models.gemini import GeminiModel

model = GeminiModel(os.getenv("MODEL_USE"), api_key=os.getenv("GEMINI_API_KEY"))
