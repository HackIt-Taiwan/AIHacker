"""
Message classifier service.
"""
from typing import Optional
from app.config import MESSAGE_TYPES
from app.ai.ai_select import create_classifier_agent

class MessageClassifier:
    def __init__(self):
        self._agent = None

    async def _ensure_agent(self):
        """Ensure the classifier agent is initialized."""
        if self._agent is None:
            self._agent = await create_classifier_agent()

    async def classify_message(self, message: str) -> str:
        """
        Classify the given message into predefined types using the classifier agent.
        Returns one of the MESSAGE_TYPES values.
        """
        try:
            await self._ensure_agent()
            result_text = ""
            
            async with self._agent.run_stream(message) as result:
                async for chunk in result.stream_text(delta=True):
                    result_text += chunk
            
            result_text = result_text.strip().lower()
            if result_text not in MESSAGE_TYPES.values():
                print(f"Invalid classification result: {result_text}")
                return MESSAGE_TYPES['UNKNOWN']

            return result_text
        except Exception as e:
            print(f"Classification error: {str(e)}")
            return MESSAGE_TYPES['UNKNOWN']