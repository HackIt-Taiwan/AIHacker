# app/summary/ai_select.py
"""
Select the AI service based on the environment variable AI_SERVICE.
"""
import importlib
import os

# TODO: Implement the ai_select_init, get_model (model getter) functions

def ai_select_init():
    service = os.getenv("AI_SERVICE")
    if not service:
        raise ValueError("No such AI service: {service}")

    module_name = f"app.ai.service.{service}"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        raise ValueError(f"Module '{module_name}' not found.") from e

    try:
        model = getattr(module, "model")
    except AttributeError as e:
        raise ValueError(f"Module '{module_name}' does not have a 'model' attribute.") from e

    return model

def get_model():
    return ai_select_init()