# app/summary/ai_select.py
"""
Select the AI service based on the environment variable AI_SERVICE.
"""
import importlib
import os
from typing import Optional
from pydantic_ai import Agent
from app.ai.agents.crazy_talk import agent_crazy
from app.ai.agents.classifier import agent_classifier
from app.ai.agents.general import agent_general
from app.ai.agents.reminder import agent_reminder
from app.ai.agents.leave import agent_leave
from app.ai.agents.faq import agent_faq

# TODO: Implement the ai_select_init, get_model (model getter) functions

def ai_select_init(service: str, model: str) -> Agent:
    """Initialize an AI model based on service type and model name."""
    if not service:
        raise ValueError(f"No such AI service: {service}")

    module_name = f"app.ai.service.{service}"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        raise ValueError(f"Module '{module_name}' not found.") from e

    try:
        model_instance = module.get_model(model)
        return model_instance
    except AttributeError as e:
        raise ValueError(f"Module '{module_name}' does not have required methods.") from e

def get_primary_model() -> Agent:
    """Get the primary AI model for main responses."""
    service = os.getenv("PRIMARY_AI_SERVICE")
    model = os.getenv("PRIMARY_MODEL")
    return ai_select_init(service, model)

def get_classifier_model() -> Agent:
    """Get the classifier AI model for message classification."""
    service = os.getenv("CLASSIFIER_AI_SERVICE")
    model = os.getenv("CLASSIFIER_MODEL")
    return ai_select_init(service, model)

async def create_classifier_agent() -> Agent:
    """Create a classifier agent with the appropriate model and prompt template."""
    model = get_classifier_model()
    agent = await agent_classifier(model)
    return agent

async def create_general_agent() -> Agent:
    """Create a general agent for search responses."""
    model = get_primary_model()
    agent = await agent_general(model)
    return agent

async def create_reminder_agent() -> Agent:
    """Create a reminder agent for handling reminders."""
    model = get_primary_model()
    agent = await agent_reminder(model)
    return agent

async def create_leave_agent() -> Agent:
    """Create a leave agent for handling leave requests."""
    model = get_primary_model()
    agent = await agent_leave(model)
    return agent

async def create_primary_agent():
    """Create the primary agent for main responses."""
    model = get_primary_model()
    agent = await agent_crazy(model)
    return agent

async def create_faq_agent() -> Agent:
    """Create a FAQ matching agent for finding relevant FAQs."""
    model = get_classifier_model()  # 使用主要模型，因為需要較強的語意理解能力
    agent = await agent_faq(model)
    return agent