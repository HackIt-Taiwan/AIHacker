"""
AI response handler.
"""
from typing import AsyncGenerator, Optional
from datetime import datetime
import re
from app.config import (
    MESSAGE_TYPES,
    AI_MAX_RETRIES,
    AI_RETRY_DELAY
)
from app.ai.ai_select import create_primary_agent, create_general_agent
from app.ai.classifier import MessageClassifier
from app.tools.search.tavily_search import TavilySearch
import asyncio
import discord

class AIHandler:
    def __init__(self, bot=None):
        self._crazy_agent = None
        self._general_agent = None
        self._classifier = None
        self._search = None
        self._bot = bot  # Store bot instance
        
    async def _ensure_services(self):
        """Ensure all required services are initialized."""
        if self._crazy_agent is None:
            self._crazy_agent = await create_primary_agent()
        if self._general_agent is None:
            self._general_agent = await create_general_agent()
        if self._classifier is None:
            self._classifier = MessageClassifier()
        if self._search is None:
            self._search = TavilySearch()

    def _clean_response(self, response: str) -> str:
        """Clean up the AI response for formatting and remove any special instructions."""
        # Remove any command patterns 
        response = re.sub(r'\[REMINDER\].*?\[/REMINDER\]', '', response, flags=re.DOTALL)
        response = re.sub(r'\[LIST_REMINDERS\]\s*\[/LIST_REMINDERS\]', '', response, flags=re.DOTALL)
        response = re.sub(r'\[DELETE_REMINDER\].*?\[/DELETE_REMINDER\]', '', response, flags=re.DOTALL)
        response = re.sub(r'\[LEAVE\].*?\[/LEAVE\]', '', response, flags=re.DOTALL)
        response = re.sub(r'\[LEAVE_LIST\]\s*\[/LEAVE_LIST\]', '', response, flags=re.DOTALL)
        response = re.sub(r'\[LEAVE_DELETE\].*?\[/LEAVE_DELETE\]', '', response, flags=re.DOTALL)
        
        # Clean up any remaining artifacts
        return response.strip()

    async def get_streaming_response(self, message: str, context: Optional[str] = None, 
                               user_id: Optional[int] = None, 
                               channel_id: Optional[int] = None,
                               guild_id: Optional[int] = None) -> AsyncGenerator[str, None]:
        """Get a streaming response from the AI."""
        await self._ensure_services()
        
        # Classify the message
        message_type = self._classifier.classify_message(message)
        
        response_buffer = ""
        
        if message_type == MESSAGE_TYPES['GENERAL']:
            # Handle general message
            async for chunk in self._general_agent.generate_stream(message, context):
                response_buffer += chunk
                yield chunk
        else:
            # Handle crazy talk
            async for chunk in self._crazy_agent.generate_stream(message, context):
                response_buffer += chunk
                yield chunk
        
        # Clean the response for internal use - but don't return it
        # Just store it if needed elsewhere
        self.last_cleaned_response = self._clean_response(response_buffer)
        # Instead of returning, we just end the generator