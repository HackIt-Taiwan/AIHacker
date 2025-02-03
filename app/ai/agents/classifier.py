# app/ai/agents/classifier.py
"""
Classifier agent configuration.
"""
from pydantic_ai import Agent

prompt = """
你是一個訊息分類器，你的工作是將用戶的訊息分類為以下類型之一：
- search: 需要搜尋網路上的資訊來回答
- chat: 一般的閒聊或情感交流
- unknown: 無法明確分類的訊息

請只回傳分類結果（小寫），不要有任何其他文字。
例如：
用戶：今天天氣如何？
回覆：search

用戶：你好啊！
回覆：chat

用戶：幫我找一下最近的新聞
回覆：search

用戶：我好難過
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