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
from app.ai.ai_select import create_primary_agent, create_general_agent, create_reminder_agent
from app.ai.classifier import MessageClassifier
from app.tools.search.tavily_search import TavilySearch
import asyncio

class AIHandler:
    def __init__(self, reminder_manager=None):
        self._crazy_agent = None
        self._general_agent = None
        self._reminder_agent = None
        self._classifier = None
        self._search = None
        self._reminder_manager = reminder_manager
        
    async def _ensure_services(self):
        """Ensure all required services are initialized."""
        if self._crazy_agent is None:
            self._crazy_agent = await create_primary_agent()
        if self._general_agent is None:
            self._general_agent = await create_general_agent()
        if self._reminder_agent is None:
            self._reminder_agent = await create_reminder_agent()
        if self._classifier is None:
            self._classifier = MessageClassifier()
        if self._search is None:
            self._search = TavilySearch()

    def _format_reminder_list(self, reminders: list) -> str:
        """Format the list of reminders into a readable string."""
        if not reminders:
            return "您目前沒有任何提醒事項。"
            
        formatted = "您的提醒事項如下：\n"
        for i, reminder in enumerate(reminders, 1):
            time_str = reminder['time'].strftime('%Y-%m-%d %H:%M')
            formatted += f"{i}. {time_str} - {reminder['task']}\n"
        return formatted

    def _clean_response(self, response: str) -> str:
        """Remove command markers and their contents from the response while preserving important messages."""
        # 先提取重要的訊息（如設定成功的回應）
        important_messages = []
        success_match = re.search(r'好的，[^[\n]*', response)
        if success_match:
            important_messages.append(success_match.group())
            
        checkmark_match = re.search(r'✅[^[\n]*', response)
        if checkmark_match:
            important_messages.append(checkmark_match.group())

        # 移除所有命令標記及其內容
        patterns = [
            # 命令標記
            r'\[REMINDER\].*?\[/REMINDER\]',
            r'\[LIST_REMINDERS\].*?\[/LIST_REMINDERS\]',
            r'\[DELETE_REMINDER\].*?\[/DELETE_REMINDER\]',
            r'\[(.*?)\]',  # 匹配任何剩餘的命令標記
            
            # 參數和時間格式
            r'TIME=.*?(?:\n|$)',  # TIME 參數
            r'TASK=.*?(?:\n|$)',  # TASK 參數
            r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}',  # 完整時間格式 (YYYY-MM-DD HH:mm)
            r'\d{1,2}-\d{2}-\d{2}\s+\d{2}:\d{2}',  # 簡短年份時間格式
            r'\d{2}:\d{2}',  # 時間格式 (HH:mm)
            r'\d{4}-\d{2}-\d{2}',  # 日期格式 (YYYY-MM-DD)
            
            # 其他清理
            r'-+\s*\n',  # 分隔線
            r'\s*\n\s*(?=\s*\n)',  # 重複的空行
        ]
        
        # 清理所有命令標記和參數
        cleaned = response
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL)
            
        # 如果清理後沒有內容，使用之前保存的重要訊息
        if not cleaned.strip() and important_messages:
            cleaned = "\n".join(important_messages)
            
        # 確保勾勾訊息前有換行
        cleaned = re.sub(r'(✅[^✅\n]*(?:\n|$))', r'\n\1', cleaned)
            
        # 移除多餘的空行，但保留勾勾訊息前的換行
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
        
        # 移除行首行尾的空白字符
        cleaned = cleaned.strip()
        
        # 最後檢查是否還有任何數字格式（可能是時間或日期）
        cleaned = re.sub(r'\b\d+[-:]\d+\b', '', cleaned)
        
        return cleaned

    async def get_streaming_response(self, message: str, context: Optional[str] = None, 
                                   user_id: Optional[int] = None, 
                                   channel_id: Optional[int] = None,
                                   guild_id: Optional[int] = None) -> AsyncGenerator[str, None]:
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
        if message_type == MESSAGE_TYPES['SEARCH']:
            agent = self._general_agent
            print("使用 general agent 回應")
        elif message_type == MESSAGE_TYPES['REMINDER']:
            agent = self._reminder_agent
            print("使用 reminder agent 回應")
        else:
            agent = self._crazy_agent
            print("使用 crazy agent 回應")
        
        response_buffer = ""
        for attempt in range(AI_MAX_RETRIES):
            try:
                async with agent.run_stream(message) as result:
                    async for chunk in result.stream_text(delta=True):
                        response_buffer += chunk
                        # 清理回應中的命令標記
                        cleaned_chunk = self._clean_response(chunk)
                        if cleaned_chunk:
                            yield cleaned_chunk
                        
                # 如果是提醒類型，解析並處理提醒相關命令
                if message_type == MESSAGE_TYPES['REMINDER'] and self._reminder_manager:
                    reminder_info = self._reminder_manager.parse_reminder(response_buffer)
                    if reminder_info:
                        command_type, time_str, task = reminder_info
                        
                        if command_type == 'add':
                            try:
                                reminder_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
                                self._reminder_manager.add_reminder(
                                    user_id, channel_id, guild_id, reminder_time, task
                                )
                                print(f"Added reminder: {time_str} - {task}")
                            except ValueError as e:
                                print(f"Error parsing reminder time: {str(e)}")
                                
                        elif command_type == 'list':
                            # 不要讓 AI 自己列出清單，而是使用系統格式
                            reminders = self._reminder_manager.get_user_reminders(user_id, guild_id)
                            formatted_list = self._format_reminder_list(reminders)
                            yield f"\n{formatted_list}"
                            
                        elif command_type == 'delete':
                            if self._reminder_manager.delete_reminder(user_id, guild_id, task):
                                print(f"Deleted reminder with task: {task}")
                            else:
                                yield f"\n找不到符合的提醒事項：{task}"
                return
                
            except Exception as e:
                if attempt == AI_MAX_RETRIES - 1:
                    print(f"AI response failed after {AI_MAX_RETRIES} attempts: {str(e)}")
                    yield f"抱歉，AI 服務暫時無法回應，請稍後再試。"
                    return
                print(f"AI response attempt {attempt + 1} failed: {str(e)}")
                await asyncio.sleep(AI_RETRY_DELAY)