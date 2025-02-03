"""
Tavily search service.
"""
from typing import Optional, Dict, Any
from tavily import TavilyClient
from app.config import TAVILY_API_KEY, TAVILY_SEARCH_MAX_RESULTS

class TavilySearch:
    def __init__(self):
        self._client = TavilyClient(api_key=TAVILY_API_KEY)

    async def search(self, query: str, max_results: Optional[int] = None) -> str:
        """
        執行搜尋並返回上下文
        """
        try:
            # 使用設定的最大結果數或預設值
            max_results = max_results or TAVILY_SEARCH_MAX_RESULTS
            
            # 獲取搜尋上下文
            print(f"Tavily search for: {query}")
            context = self._client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced"
            )
            
            return context
            
        except Exception as e:
            print(f"Tavily search error: {str(e)}")
            return f"搜尋時發生錯誤: {str(e)}"
