"""
Notion FAQ service for retrieving and managing FAQ data.
"""
from typing import List, Dict, Optional
from notion_client import Client
from app.config import NOTION_API_KEY, NOTION_FAQ_PAGE_ID

class NotionFAQ:
    def __init__(self):
        self.client = Client(auth=NOTION_API_KEY)
        self.faq_page_id = NOTION_FAQ_PAGE_ID
        self._cache = None
        self._last_update = None

    async def get_all_faqs(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get all FAQs from the Notion database.
        
        Args:
            force_refresh: Whether to force a refresh of the cache
            
        Returns:
            List of FAQ items with question and answer
        """
        try:
            # Query the database
            response = self.client.databases.query(
                database_id=self.faq_page_id,
                sorts=[{
                    "timestamp": "last_edited_time",
                    "direction": "descending"
                }]
            )

            faqs = []
            for page in response["results"]:
                # Extract question and answer from the page properties
                question = self._get_text_content(page["properties"].get("Question", {}))
                answer = self._get_text_content(page["properties"].get("Answer", {}))
                
                if question and answer:
                    faqs.append({
                        "question": question,
                        "answer": answer,
                        "category": self._get_text_content(page["properties"].get("Category", {})),
                        "tags": self._get_multi_select_values(page["properties"].get("Tags", {}))
                    })

            return faqs

        except Exception as e:
            print(f"Error fetching FAQs from Notion: {str(e)}")
            return []

    def _get_text_content(self, property_data: Dict) -> str:
        """Extract text content from a Notion property."""
        try:
            if property_data["type"] == "title":
                return " ".join([text["text"]["content"] for text in property_data["title"]])
            elif property_data["type"] == "rich_text":
                return " ".join([text["text"]["content"] for text in property_data["rich_text"]])
            return ""
        except (KeyError, TypeError):
            return ""

    def _get_multi_select_values(self, property_data: Dict) -> List[str]:
        """Extract values from a multi-select property."""
        try:
            if property_data["type"] == "multi_select":
                return [option["name"] for option in property_data["multi_select"]]
            return []
        except (KeyError, TypeError):
            return []

    async def find_matching_faq(self, question: str) -> Optional[Dict]:
        """
        Find a matching FAQ for the given question using AI comparison.
        
        Args:
            question: The question to find a match for
            
        Returns:
            Matching FAQ item if found, None otherwise
        """
        try:
            # Get all FAQs
            faqs = await self.get_all_faqs()
            if not faqs:
                return None

            # Prepare the prompt for AI
            prompt = f"""以下是我們的 FAQ 列表：

{self._format_faqs_for_prompt(faqs)}

用戶問題：{question}

請判斷這個問題是否已經包含在上述 FAQ 中。如果是，請回傳 FAQ 的編號（例如：1）；如果不是，請回傳 "none"。
只需要回傳數字或 "none"，不需要其他解釋。"""

            # Use the classifier AI to determine if there's a match
            from app.ai.ai_select import create_classifier_agent
            classifier = await create_classifier_agent()
            
            async with classifier.run_stream(prompt) as result:
                response = ""
                async for chunk in result.stream_text(delta=True):
                    response += chunk
                
            response = response.strip().lower()
            
            # If we got a number, return the corresponding FAQ
            try:
                index = int(response) - 1
                if 0 <= index < len(faqs):
                    return faqs[index]
            except ValueError:
                pass
                
            return None

        except Exception as e:
            print(f"Error finding matching FAQ: {str(e)}")
            return None

    def _format_faqs_for_prompt(self, faqs: List[Dict]) -> str:
        """Format FAQs for the AI prompt."""
        formatted = []
        for i, faq in enumerate(faqs, 1):
            formatted.append(f"{i}. Q: {faq['question']}\nA: {faq['answer']}\n")
        return "\n".join(formatted) 