from typing import AsyncGenerator
import os
import asyncio
from app.ai.agents.general import agent_general
from pydantic_ai import Agent, RunContext
from typing_extensions import TypedDict

class MessageResponse(TypedDict, total=False):
    content: str

class AIHandler:
    def __init__(self):
        self._agent = None

    async def _ensure_agent(self):
        if self._agent is None:
            self._agent = await agent_general()

    async def get_streaming_response(self, message: str) -> AsyncGenerator[str, None]:
        """
        Get streaming response from the AI service using PydanticAI's streaming approach
        """
        MAX_RETRIES = 5
        RETRY_DELAY = 15  # seconds
        retries = 0

        await self._ensure_agent()

        while retries < MAX_RETRIES:
            try:
                async with self._agent.run_stream(message) as result:
                    async for message in result.stream_text(delta=True):
                        print(f"{message}")  # Debug logging
                        yield message
                            
                # If we get here, the response was successful
                break
                    
            except Exception as e:
                retries += 1
                print(f"Error in getting AI response (attempt {retries}/{MAX_RETRIES}): {str(e)}")
                
                if retries < MAX_RETRIES:
                    print(f"Retrying in {RETRY_DELAY} seconds...")
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    yield f"抱歉，AI 服務暫時無法回應，請稍後再試。"