# app/summary/agents/general.py
"""
General agent.
"""
import os

from pydantic_ai import Agent

from app.ai.ai_select import get_model

prompt = """
你是 HackIt 的專屬 AI 精靈，你叫做 Hackster。
你的目標是幫助使用者解惑。
"""

async def agent_general() -> str:
    model = get_model()
    agent_prompt = (
        prompt
        + f"\n請直接用繁體中文回答"
    )
    agent = Agent(model, system_prompt=agent_prompt)
    return agent
