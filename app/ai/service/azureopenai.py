# app/agents/service/azure.py
"""
Azure OpenAI service integration.
"""
import os

from openai import AsyncAzureOpenAI
from pydantic_ai.models.openai import OpenAIModel

client = AsyncAzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY")
)

model = OpenAIModel(os.getenv("MODEL_USE"), openai_client=client)
