"""
AI response handler.
"""
from typing import AsyncGenerator, Optional
from datetime import datetime
import re
from app.config import (
    MESSAGE_TYPES,
    AI_MAX_RETRIES,
    AI_RETRY_DELAY,
    LEAVE_ANNOUNCEMENT_CHANNEL_IDS,
    LEAVE_ALLOWED_ROLES
)
from app.ai.ai_select import create_primary_agent, create_general_agent, create_reminder_agent, create_leave_agent
from app.ai.classifier import MessageClassifier
from app.tools.search.tavily_search import TavilySearch
import asyncio
import discord

class AIHandler:
    def __init__(self, reminder_manager=None, leave_manager=None, bot=None):
        self._crazy_agent = None
        self._general_agent = None
        self._reminder_agent = None
        self._leave_agent = None
        self._classifier = None
        self._search = None
        self._reminder_manager = reminder_manager
        self._leave_manager = leave_manager
        self._bot = bot  # 保存 bot 實例以便發送公告
        
    async def _ensure_services(self):
        """Ensure all required services are initialized."""
        if self._crazy_agent is None:
            self._crazy_agent = await create_primary_agent()
        if self._general_agent is None:
            self._general_agent = await create_general_agent()
        if self._reminder_agent is None:
            self._reminder_agent = await create_reminder_agent()
        if self._leave_agent is None:
            self._leave_agent = await create_leave_agent()
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
        success_match = re.findall(r'好的，[^[\n]*', response)
        if success_match:
            important_messages.extend(success_match)
            
        checkmark_match = re.findall(r'✅[^[\n]*', response)
        if checkmark_match:
            important_messages.extend(checkmark_match)

        # 移除所有命令標記及其內容
        patterns = [
            # 命令標記
            r'\[REMINDER\].*?\[/REMINDER\]',
            r'\[LIST_REMINDERS\].*?\[/LIST_REMINDERS\]',
            r'\[DELETE_REMINDER\].*?\[/DELETE_REMINDER\]',
            r'\[LEAVE\].*?\[/LEAVE\]',
            r'\[LIST_LEAVES\].*?\[/LIST_LEAVES\]',
            r'\[DELETE_LEAVE\].*?\[/DELETE_LEAVE\]',
            r'\[(.*?)\]',  # 匹配任何剩餘的命令標記
            
            # 參數和時間格式
            r'TIME=.*?(?:\n|$)',  # TIME 參數
            r'TASK=.*?(?:\n|$)',  # TASK 參數
            r'START_DATE=.*?(?:\n|$)',  # START_DATE 參數
            r'END_DATE=.*?(?:\n|$)',  # END_DATE 參數
            r'REASON=.*?(?:\n|$)',  # REASON 參數
            r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}',  # 完整時間格式 (YYYY-MM-DD HH:mm)
            r'\d{1,2}-\d{2}-\d{2}\s+\d{2}:\d{2}',  # 簡短年份時間格式
            r'\d{2}:\d{2}',  # 時間格式 (HH:mm)
            r'\d{4}-\d{2}-\d{2}',  # 日期格式 (YYYY-MM-DD)
            
            # 其他清理
            r'-+\s*\n',  # 分隔線
            r'\s*\n\s*(?=\s*\n)',  # 重複的空行
        ]
        
        # 移除所有命令標記及其內容
        cleaned = response
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE)
            
        # 保留重要訊息
        if important_messages:
            cleaned = cleaned.strip() + '\n' + '\n'.join(important_messages)
            
        return cleaned.strip()

    async def get_streaming_response(self, message: str, context: Optional[str] = None, 
                                   user_id: Optional[int] = None, 
                                   channel_id: Optional[int] = None,
                                   guild_id: Optional[int] = None) -> AsyncGenerator[str, None]:
        """
        Get a streaming response from the AI.
        First classifies the message type, then handles it accordingly.
        """
        try:
            await self._ensure_services()
            
            # 檢查是否為請假相關的訊息
            message_type = await self._classifier.classify_message(message)
            if message_type == MESSAGE_TYPES['LEAVE']:
                # 檢查用戶是否有請假權限
                if not self._bot or not guild_id or not user_id:
                    yield "❌ 無法處理請假請求，請確保在伺服器中使用此功能。"
                    return
                
                guild = self._bot.get_guild(guild_id)
                if not guild:
                    yield "❌ 無法找到伺服器資訊。"
                    return
                    
                member = guild.get_member(user_id)
                if not member:
                    yield "❌ 無法找到您的成員資訊。"
                    return
                
                # 檢查是否有允許的身份組
                if not any(role.id in LEAVE_ALLOWED_ROLES for role in member.roles):
                    yield "❌ 您沒有使用請假功能的權限。需要特定的身份組才能使用此功能。"
                    return

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
            agent = None
            if message_type == MESSAGE_TYPES['SEARCH']:
                agent = self._general_agent
                print("使用 general agent 回應")
            elif message_type == MESSAGE_TYPES['REMINDER']:
                agent = self._reminder_agent
                print("使用 reminder agent 回應")
            elif message_type == MESSAGE_TYPES['LEAVE']:
                agent = self._leave_agent
                print("使用 leave agent 回應")
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
                        # 允許處理多個命令
                        while True:
                            reminder_info = self._reminder_manager.parse_reminder(response_buffer)
                            if not reminder_info:
                                break
                                
                            command_type, time_str, task, matched_command = reminder_info
                            
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
                                
                                # 將提醒清單添加到 AI 的輸入中，讓 AI 可以繼續處理後續命令
                                message += f"\n\n以下是您目前所有的提醒事項：\n{formatted_list}"
                                
                                # 重新調用 AI，讓它處理後續命令
                                async with agent.run_stream(message) as result:
                                    async for chunk in result.stream_text(delta=True):
                                        response_buffer += chunk
                                        cleaned_chunk = self._clean_response(chunk)
                                        if cleaned_chunk:
                                            yield cleaned_chunk
                                            
                            elif command_type == 'delete':
                                # 根據刪除命令的條件（時間和/或任務內容）查找匹配的提醒
                                matching_reminders = self._reminder_manager.find_reminders(
                                    user_id, guild_id, task if task else None, time_str if time_str else None
                                )
                                
                                if not matching_reminders:
                                    yield "\n找不到符合的提醒事項，請確認您的刪除條件。"
                                else:
                                    yield "\n根據您的刪除條件，找到以下提醒："
                                    for reminder in matching_reminders:
                                        formatted_time = reminder['time'].strftime('%Y-%m-%d %H:%M')
                                        yield f"\n- {formatted_time} - {reminder['task']}"
                                        
                                        # 刪除並顯示刪除結果
                                        if self._reminder_manager.delete_reminder_by_id(user_id, guild_id, reminder['id']):
                                            yield f"\n✅ 已刪除提醒：{formatted_time} - {reminder['task']}"
                                        else:
                                            yield f"\n❌ 刪除提醒失敗：{formatted_time} - {reminder['task']}"
                                            
                            # 移除已處理的命令
                            response_buffer = response_buffer.replace(matched_command, '')

                    # 如果是請假類型，解析並處理請假相關命令
                    elif message_type == MESSAGE_TYPES['LEAVE'] and self._leave_manager:
                        # 允許處理多個命令
                        while True:
                            # 使用正則表達式找出所有命令
                            leave_match = re.search(r'\[LEAVE\](.*?)\[/LEAVE\]', response_buffer, re.DOTALL)
                            list_match = re.search(r'\[LIST_LEAVES\](.*?)\[/LIST_LEAVES\]', response_buffer, re.DOTALL)
                            delete_match = re.search(r'\[DELETE_LEAVE\](.*?)\[/DELETE_LEAVE\]', response_buffer, re.DOTALL)
                            
                            if leave_match:
                                command_text = leave_match.group(1).strip()
                                start_date = re.search(r'START_DATE=(\d{4}-\d{2}-\d{2})', command_text)
                                end_date = re.search(r'END_DATE=(\d{4}-\d{2}-\d{2})', command_text)
                                reason = re.search(r'REASON=(.*?)(?:\n|$)', command_text)
                                deputy = re.search(r'DEPUTY=<@(\d+)>', command_text)
                                
                                if start_date and end_date:
                                    start = datetime.strptime(start_date.group(1), '%Y-%m-%d')
                                    end = datetime.strptime(end_date.group(1), '%Y-%m-%d')
                                    reason_text = reason.group(1) if reason else None
                                    deputy_id = int(deputy.group(1)) if deputy else None
                                    
                                    if self._leave_manager.add_leave(
                                        user_id, guild_id, start, end, reason_text, deputy_id
                                    ):
                                        yield "\n✅ 已為您申請請假"
                                        # 發送請假公告
                                        await self.send_leave_announcement(
                                            user_id,
                                            guild_id,
                                            start,
                                            end,
                                            reason_text,
                                            deputy_id
                                        )
                                    else:
                                        yield "\n❌ 請假申請失敗，可能與現有請假時間重疊"
                                        
                                response_buffer = response_buffer.replace(leave_match.group(0), '')
                                
                            elif list_match:
                                leaves = self._leave_manager.get_user_leaves(user_id, guild_id)
                                if not leaves:
                                    yield "\n📅 您目前沒有請假記錄。"
                                else:
                                    yield "\n📅 您的請假記錄：\n\n"
                                    for leave in leaves:
                                        yield (
                                            f"🔸 {leave['start_date'].strftime('%Y-%m-%d')} 至 "
                                            f"{leave['end_date'].strftime('%Y-%m-%d')}\n"
                                        )
                                        if leave['reason']:
                                            yield f"📝 原因：{leave['reason']}\n"
                                        yield "\n"
                                        
                                response_buffer = response_buffer.replace(list_match.group(0), '')
                                
                            elif delete_match:
                                command_text = delete_match.group(1).strip()
                                start_date = re.search(r'START_DATE=(\d{4}-\d{2}-\d{2})', command_text)
                                end_date = re.search(r'END_DATE=(\d{4}-\d{2}-\d{2})', command_text)
                                reason = re.search(r'REASON=(.*?)(?:\n|$)', command_text)
                                
                                leaves = self._leave_manager.get_user_leaves(user_id, guild_id)
                                deleted_count = 0
                                
                                for leave in leaves:
                                    should_delete = True
                                    
                                    if start_date and leave['start_date'].strftime('%Y-%m-%d') != start_date.group(1):
                                        should_delete = False
                                    if end_date and leave['end_date'].strftime('%Y-%m-%d') != end_date.group(1):
                                        should_delete = False
                                    if reason and leave['reason'] != reason.group(1):
                                        should_delete = False
                                        
                                    if should_delete:
                                        if self._leave_manager.delete_leave(leave['id'], user_id, guild_id):
                                            deleted_count += 1
                                
                                if deleted_count > 0:
                                    yield f"\n✅ 已刪除 {deleted_count} 筆請假記錄"
                                else:
                                    yield "\n❌ 找不到符合條件的請假記錄"
                                    
                                response_buffer = response_buffer.replace(delete_match.group(0), '')
                                
                            else:
                                break
                    return
                    
                except Exception as e:
                    if attempt == AI_MAX_RETRIES - 1:
                        print(f"AI response failed after {AI_MAX_RETRIES} attempts: {str(e)}")
                        yield f"抱歉，AI 服務暫時無法回應，請稍後再試。"
                        return
                    print(f"AI response attempt {attempt + 1} failed: {str(e)}")
                    await asyncio.sleep(AI_RETRY_DELAY)

        except Exception as e:
            print(f"處理訊息時發生錯誤：{str(e)}")
            yield f"抱歉，AI 服務暫時無法回應，請稍後再試。"

    async def handle_command(self, command_type: str, command_data: dict) -> AsyncGenerator[str, None]:
        if command_type == "list_reminders":
            reminders = await self._reminder_manager.get_reminders()
            if not reminders:
                yield "目前沒有任何提醒事項"
                return
            
            formatted_reminders = "\n".join([
                f"時間：{r['time']} 提醒：{r['task']}"
                for r in reminders
            ])
            yield f"以下是您目前的提醒事項：\n{formatted_reminders}"
            
            # 如果這是刪除流程的一部分，將提醒清單添加到AI的上下文中
            if command_data.get("is_delete_flow"):
                delete_context = f"""
                以下是用戶目前的提醒清單：
                {formatted_reminders}
                
                請根據用戶的要求刪除相應的提醒。
                """
                # 重新調用AI來處理刪除命令
                response = await self.get_streaming_response(delete_context)
                async for msg in response:
                    yield msg

        elif command_type == "delete_reminder":
            # 首先列出所有提醒
            async for msg in self.handle_command("list_reminders", {"is_delete_flow": True}):
                yield msg

    async def send_leave_announcement(self, user_id: int, guild_id: int, start_date: datetime, end_date: datetime, reason: str = None, deputy_id: int = None):
        """發送請假公告到指定頻道"""
        if not self._bot or not LEAVE_ANNOUNCEMENT_CHANNEL_IDS:
            return

        guild = self._bot.get_guild(guild_id)
        if not guild:
            return

        member = guild.get_member(user_id)
        if not member:
            return

        # 檢查請假狀態
        status = self._leave_manager.get_leave_status(start_date, end_date)
        
        # 根據狀態設置顏色
        if status == 'pending':
            color = discord.Color.light_grey()
        elif status == 'active':
            color = discord.Color.blue()
        else:  # expired
            color = discord.Color.dark_grey()

        # 創建 embed 物件
        embed = discord.Embed(
            title="📢 請假公告",
            description=f"{member.mention} 已申請請假",
            color=color,
            timestamp=datetime.now()
        )

        # 添加請假資訊
        embed.add_field(
            name="⏰ 請假期間",
            value=f"從 {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
            inline=False
        )

        if reason:
            embed.add_field(
                name="📝 請假原因",
                value=reason,
                inline=False
            )

        # 如果有代理人，添加代理人資訊
        if deputy_id:
            deputy = guild.get_member(deputy_id)
            if deputy:
                embed.add_field(
                    name="👥 代理人",
                    value=deputy.mention,
                    inline=False
                )

        # 設置請假者的頭像
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # 添加頁腳
        embed.set_footer(text=f"請假申請時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 在所有配置的公告頻道發送公告
        for channel_id in LEAVE_ANNOUNCEMENT_CHANNEL_IDS:
            try:
                channel = self._bot.get_channel(channel_id)
                if channel and isinstance(channel, discord.TextChannel):
                    msg = await channel.send(embed=embed)
                    
                    # 創建討論串
                    thread = await msg.create_thread(
                        name=f"{member.display_name}的請假討論串",
                        reason="請假期間的相關討論"
                    )
                    
                    # 在討論串發送初始訊息
                    initial_message = (
                        f"這是 {member.mention} 的請假討論串。\n"
                        f"請假期間：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
                    )
                    if deputy_id:
                        deputy = guild.get_member(deputy_id)
                        if deputy:
                            initial_message += f"\n代理人：{deputy.mention}"
                    initial_message += f"\n如果有任何事情要找 {member.mention}，請於此討論串留言。"
                    
                    await thread.send(initial_message)
                    
                    # 獲取最新的請假記錄
                    leaves = self._leave_manager.get_user_leaves(user_id, guild_id)
                    if leaves:
                        latest_leave = leaves[0]
                        self._leave_manager.update_announcement_message(latest_leave['id'], msg.id, channel_id)
                        self._leave_manager.update_thread_id(latest_leave['id'], thread.id)
                        print(f"已更新請假記錄 {latest_leave['id']} 的討論串ID：{thread.id}")
                        
            except Exception as e:
                print(f"發送請假公告到頻道 {channel_id} 時發生錯誤：{str(e)}")

    async def update_leave_announcements(self):
        """更新所有請假公告的狀態"""
        try:
            # 確保 leave_manager 已初始化
            if self._leave_manager is None:
                print("警告：請假管理器尚未初始化，無法更新請假公告")
                return
                
            # 獲取所有活動的請假記錄
            leaves = self._leave_manager.get_all_active_leaves()
            
            for leave in leaves:
                # 檢查請假狀態
                status = self._leave_manager.get_leave_status(
                    leave['start_date'],
                    leave['end_date']
                )
                
                # 獲取公告訊息資訊
                if not leave['announcement_msg_id'] or not leave['announcement_channel_id']:
                    continue
                    
                channel = self._bot.get_channel(leave['announcement_channel_id'])
                if not channel:
                    continue
                    
                try:
                    message = await channel.fetch_message(leave['announcement_msg_id'])
                    if not message:
                        continue
                        
                    if status == 'expired':
                        # 將過期的請假記錄轉換為純文字格式
                        guild = self._bot.get_guild(leave['guild_id'])
                        if not guild:
                            continue
                            
                        member = guild.get_member(leave['user_id'])
                        if not member:
                            continue
                            
                        formatted_text = (
                            f"🗓️ **已結束的請假記錄** | "
                            f"{member.display_name} | "
                            f"{leave['start_date'].strftime('%Y-%m-%d')} → "
                            f"{leave['end_date'].strftime('%Y-%m-%d')}"
                        )
                        if leave['reason']:
                            formatted_text += f" | 原因：{leave['reason']}"
                            
                        await message.edit(content=formatted_text, embed=None)
                    else:
                        # 更新 embed 顏色
                        embed = message.embeds[0]
                        if status == 'pending':
                            embed.color = discord.Color.light_grey()
                        else:  # active
                            embed.color = discord.Color.blue()
                        await message.edit(embed=embed)
                        
                except discord.NotFound:
                    print(f"無法找到訊息 ID: {leave['announcement_msg_id']}")
                except discord.Forbidden:
                    print(f"沒有權限編輯訊息 ID: {leave['announcement_msg_id']}")
                except Exception as e:
                    print(f"更新請假公告時發生錯誤：{str(e)}")
                    
        except Exception as e:
            print(f"更新請假公告時發生錯誤：{str(e)}")

    async def start_leave_announcement_updater(self):
        """開始定期更新請假公告"""
        while True:
            await self.update_leave_announcements()
            await asyncio.sleep(3600)  # 每小時檢查一次

    async def handle_mention_of_leave_user(self, message: discord.Message, mention: discord.Member, leave_info: dict):
        """處理有人提及請假中的使用者"""
        try:
            # 獲取討論串資訊
            thread_info = self._leave_manager.get_leave_thread(mention.id, message.guild.id)
            print(f"獲取到的討論串資訊：{thread_info}")
            
            # 檢查最近15則訊息是否已經提醒過
            has_recent_notification = False
            try:
                async for msg in message.channel.history(limit=15):
                    if msg.author == self._bot.user and msg.reference and msg.reference.message_id:
                        try:
                            referenced_msg = await message.channel.fetch_message(msg.reference.message_id)
                            if referenced_msg and mention in referenced_msg.mentions:
                                has_recent_notification = True
                                break
                        except:
                            continue
            except Exception as e:
                print(f"檢查歷史訊息時發生錯誤：{str(e)}")
            
            if not thread_info or not thread_info.get('thread_id'):
                print(f"找不到 {mention.display_name} 的請假討論串")
                # 如果找不到討論串，且最近沒有提醒過，才顯示基本的請假資訊
                if not has_recent_notification:
                    await message.reply(
                        f"⚠️ {mention.display_name} 目前正在請假中\n"
                        f"📅 請假期間：{leave_info['start_date'].strftime('%Y-%m-%d')} 至 "
                        f"{leave_info['end_date'].strftime('%Y-%m-%d')}"
                    )
                return
            
            # 建立討論串連結
            thread_url = f"https://discord.com/channels/{message.guild.id}/{thread_info['thread_id']}"
            message_url = message.jump_url
            
            print(f"討論串連結：{thread_url}")
            print(f"原始訊息連結：{message_url}")
            
            # 只有在最近沒有提醒過的情況下才回覆
            if not has_recent_notification:
                reply_message = (
                    f"⚠️ {mention.display_name} 目前正在請假中\n"
                    f"📅 請假期間：{leave_info['start_date'].strftime('%Y-%m-%d')} 至 "
                    f"{leave_info['end_date'].strftime('%Y-%m-%d')}\n"
                )
                
                # 如果有代理人，加入代理人資訊
                if leave_info.get('deputy_id'):
                    deputy = message.guild.get_member(leave_info['deputy_id'])
                    if deputy:
                        reply_message += f"👥 代理人：{deputy.mention}\n"
                
                reply_message += f"💬 請在請假討論串留言：{thread_url}"
                await message.reply(reply_message)
            
            # 在討論串中發送通知
            try:
                # 獲取父頻道
                channel = self._bot.get_channel(thread_info['channel_id'])
                if not channel:
                    print(f"找不到頻道 {thread_info['channel_id']}")
                    return

                # 直接從 guild 獲取討論串
                thread = message.guild.get_thread(thread_info['thread_id'])
                if not thread:
                    print(f"找不到討論串 {thread_info['thread_id']}")
                    return
                
                # 準備訊息預覽，替換提及為可讀名稱
                preview = f"{message.author.display_name}: {message.content}"
                # 替換所有使用者提及
                for user in message.mentions:
                    preview = preview.replace(f'<@{user.id}>', user.display_name)
                # 替換所有頻道提及
                for channel_mention in message.channel_mentions:
                    preview = preview.replace(f'<#{channel_mention.id}>', f'#{channel_mention.name}')
                # 替換所有身分組提及
                for role in message.role_mentions:
                    preview = preview.replace(f'<@&{role.id}>', f'@{role.name}')
                
                # 如果訊息太長，截斷並加上...
                if len(preview) > 100:
                    # 保留發言者名稱，只截斷訊息內容
                    author_part = f"{message.author.display_name}: "
                    content_part = preview[len(author_part):]
                    preview = author_part + content_part[:97-len(author_part)] + "..."
                # 限制行數
                preview_lines = preview.split('\n')
                if len(preview_lines) > 3:
                    preview = '\n'.join(preview_lines[:3]) + "\n..."
                
                thread_message = (
                    f"----------------------------------\n"
                    f"⚠️ {message.author.mention} 在 {message.channel.mention} "
                    f"提及了 {mention.mention}\n"
                    f"🔗 原始訊息：{message_url}\n"
                    f"```\n{preview}\n```"
                )
                
                # 如果有代理人，也要提及代理人
                if leave_info.get('deputy_id'):
                    deputy = message.guild.get_member(leave_info['deputy_id'])
                    if deputy:
                        thread_message = thread_message + f"👥 cc: {deputy.mention}"
                
                await thread.send(thread_message)
                print(f"已在討論串中發送通知")
                
            except discord.NotFound:
                print(f"找不到討論串或頻道")
            except discord.Forbidden:
                print(f"沒有權限訪問討論串")
            except Exception as e:
                print(f"在討論串中發送通知時發生錯誤：{str(e)}")
                
        except Exception as e:
            print(f"處理請假者被提及時發生錯誤：{str(e)}")
            # 發生錯誤時，如果最近沒有提醒過，才顯示基本的請假資訊
            if not has_recent_notification:
                await message.reply(
                    f"⚠️ {mention.display_name} 目前正在請假中\n"
                    f"📅 請假期間：{leave_info['start_date'].strftime('%Y-%m-%d')} 至 "
                    f"{leave_info['end_date'].strftime('%Y-%m-%d')}"
                )