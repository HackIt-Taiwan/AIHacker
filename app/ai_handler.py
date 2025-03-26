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
        # response = re.sub(r'\[REMINDER\].*?\[/REMINDER\]', '', response, flags=re.DOTALL)
        # response = re.sub(r'\[LIST_REMINDERS\]\s*\[/LIST_REMINDERS\]', '', response, flags=re.DOTALL)
        # response = re.sub(r'\[DELETE_REMINDER\].*?\[/DELETE_REMINDER\]', '', response, flags=re.DOTALL)
        # response = re.sub(r'\[LEAVE\].*?\[/LEAVE\]', '', response, flags=re.DOTALL)
        # response = re.sub(r'\[LEAVE_LIST\]\s*\[/LEAVE_LIST\]', '', response, flags=re.DOTALL)
        # response = re.sub(r'\[LEAVE_DELETE\].*?\[/LEAVE_DELETE\]', '', response, flags=re.DOTALL)
        
        # Clean up any remaining artifacts
        return response.strip()

    async def get_streaming_response(self, message: str, context: Optional[str] = None, 
                               user_id: Optional[int] = None, 
                               channel_id: Optional[int] = None,
                               guild_id: Optional[int] = None) -> AsyncGenerator[str, None]:
        """Get a streaming response from the AI."""
        await self._ensure_services()
        
        # Classify the message
        message_type = await self._classifier.classify_message(message)
        
        response_buffer = ""
        
        if message_type == MESSAGE_TYPES['GENERAL']:
            # Handle general message
            agent = self._general_agent
            print("Using general agent")
        else:
            # Handle crazy talk
            agent = self._crazy_agent
            print("Using crazy agent")
        
        response_buffer = ""
        try:
            for attempt in range(AI_MAX_RETRIES):
                try:
                    async with agent.run_stream(message) as result:
                        async for chunk in result.stream_text(delta=True):
                            response_buffer += chunk
                            # 清理回應中的命令標記
                            cleaned_chunk = self._clean_response(chunk)
                            if cleaned_chunk:
                                yield cleaned_chunk
                    return
                    
                except Exception as e:
                    if attempt == AI_MAX_RETRIES - 1:
                        print(f"AI response failed after {AI_MAX_RETRIES} attempts: {str(e)}")
                        yield f"抱歉，AI 服務暫時無法回應，請稍後再試。"
                        return
                    print(f"AI response attempt {attempt + 1} failed: {str(e)}")
                    await asyncio.sleep(AI_RETRY_DELAY)

        except Exception as e:
            print(f"處理訊息時發生錯誤：{str(e)}")
            yield f"抱歉，AI 服務暫時無法回應，請稍後再試。"