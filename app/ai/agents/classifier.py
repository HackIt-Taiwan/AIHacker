# app/ai/agents/classifier.py
"""
Classifier agent configuration.
"""
from pydantic_ai import Agent

prompt = """
你是一個訊息分類器，你的工作是將用戶的訊息分類為以下類型之一：
- search: 需要搜尋網路上的資訊來回答
- chat: 一般的閒聊或情感交流
- reminder: 與提醒事項相關的操作（包括設定新提醒、查看提醒列表、刪除提醒）
- unknown: 無法明確分類的訊息

請只回傳分類結果（小寫），不要有任何其他文字。

提醒相關的範例：
用戶：提醒我明天早上九點開會
回覆：reminder

用戶：三小時後提醒我關火
回覆：reminder

用戶：幫我看看目前有什麼提醒
回覆：reminder

用戶：顯示所有提醒事項
回覆：reminder

用戶：刪除開會的提醒
回覆：reminder

用戶：幫我取消關火的提醒
回覆：reminder

一般對話的範例：
用戶：今天天氣如何？
回覆：search

用戶：你好啊！
回覆：chat

用戶：幫我找一下最近的新聞
回覆：search

用戶：我好難過
回覆：chat

用戶：你覺得人工智能會取代人類嗎
回覆：chat

現在請分類這個訊息：{message}
"""

async def agent_classifier(model) -> Agent:
    """Create a classifier agent with the appropriate model and prompt template."""
    # Set up the agent with classification-specific settings
    model.temperature = 0.3
    model.max_tokens = 10
    
    # Create agent with the classifier prompt
    agent = Agent(model, system_prompt=prompt)
    return agent 