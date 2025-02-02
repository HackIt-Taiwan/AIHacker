from typing import AsyncGenerator
import os
import asyncio
from app.ai.agents.crazy_talk import agent_crazy
from pydantic_ai import Agent, RunContext
from typing_extensions import TypedDict
from app.config import (
    AI_MAX_RETRIES,
    AI_RETRY_DELAY
)

class MessageResponse(TypedDict, total=False):
    content: str

class AIHandler:
    def __init__(self):
        self._agent = None

    async def _ensure_agent(self):
        if self._agent is None:
            self._agent = await agent_crazy()

    async def get_streaming_response(self, message: str) -> AsyncGenerator[str, None]:
        """
        Get streaming response from the AI service using PydanticAI's streaming approach
        """
        retries = 0

        await self._ensure_agent()
        print("使用瘋狂模式回應")

        while retries < AI_MAX_RETRIES:
            try:
                async with self._agent.run_stream(message) as result:
                    async for message in result.stream_text(delta=True):
                        print(f"{message}")  # Debug logging
                        yield message
                            
                # If we get here, the response was successful
                break
                    
            except Exception as e:
                retries += 1
                print(f"Error in getting AI response (attempt {retries}/{AI_MAX_RETRIES}): {str(e)}")
                
                if retries < AI_MAX_RETRIES:
                    print(f"Retrying in {AI_RETRY_DELAY} seconds...")
                    await asyncio.sleep(AI_RETRY_DELAY)
                else:
                    yield f"抱歉，AI 服務暫時無法回應，請稍後再試。"