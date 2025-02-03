"""
AI response handler.
"""
from typing import AsyncGenerator, Optional
from app.config import (
    MESSAGE_TYPES,
    AI_MAX_RETRIES,
    AI_RETRY_DELAY
)
from app.ai.ai_select import create_primary_agent, create_general_agent
from app.ai.classifier import MessageClassifier
from app.tools.search.tavily_search import TavilySearch
import asyncio

class AIHandler:
    def __init__(self):
        self._crazy_agent = None
        self._general_agent = None
        self._classifier = None
        self._search = None
        
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

    async def get_streaming_response(self, message: str, context: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Get a streaming response from the AI.
        First classifies the message type, then handles it accordingly.
        """
        await self._ensure_services()
        
        # 先進行訊息分類
        message_type = await self._classifier.classify_message(message)
        print(f"Message classified as: {message_type}")
        
        # 如果需要搜尋，先獲取搜尋結果
        search_context = ""
        if message_type == MESSAGE_TYPES['SEARCH']:
            search_context = await self._search.search(context)
            if context:
                context = f"\n-------------------\n\n問題：\n{context}\n\n搜尋結果：\n{search_context}\n\n----------------請你根據此搜尋結果回應使用者的問題。"
            else:
                context = f"\n搜尋結果：\n{search_context}"
            
            message += context
        
        # 根據消息類型選擇使用的 agent
        agent = self._general_agent if message_type == MESSAGE_TYPES['SEARCH'] else self._crazy_agent
        print(f"使用 {'general' if message_type == MESSAGE_TYPES['SEARCH'] else 'crazy'} agent 回應")
        
        for attempt in range(AI_MAX_RETRIES):
            try:
                async with agent.run_stream(message) as result:
                    async for message in result.stream_text(delta=True):
                        print(f"{message}")  # Debug logging
                        yield message
                return
            except Exception as e:
                if attempt == AI_MAX_RETRIES - 1:
                    print(f"AI response failed after {AI_MAX_RETRIES} attempts: {str(e)}")
                    yield f"抱歉，AI 服務暫時無法回應，請稍後再試。"
                    return
                print(f"AI response attempt {attempt + 1} failed: {str(e)}")
                await asyncio.sleep(AI_RETRY_DELAY)