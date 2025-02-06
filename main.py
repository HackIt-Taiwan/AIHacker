import discord
from discord.ext import commands
import asyncio
from collections import defaultdict
import time
import random
from typing import Dict, List
from datetime import datetime, timedelta
import re

from app.config import (
    DISCORD_TOKEN, TYPING_INTERVAL, STREAM_CHUNK_SIZE,
    RATE_LIMIT_MESSAGES, RATE_LIMIT_PERIOD, RATE_LIMIT_ERROR,
    MAX_MESSAGE_LENGTH, MIN_MESSAGE_LENGTH, IGNORED_PREFIXES,
    RANDOM_REPLY_CHANCE, STREAM_UPDATE_INTERVAL, STREAM_MIN_UPDATE_LENGTH,
    STREAM_UPDATE_CHARS, SPLIT_CHARS, BOT_ACTIVITY, BOT_THINKING_MESSAGE,
    BOT_RANDOM_THINKING_MESSAGE, CHAT_HISTORY_TARGET_CHARS,
    CHAT_HISTORY_MAX_MESSAGES, HISTORY_PROMPT_TEMPLATE,
    RANDOM_PROMPT_TEMPLATE, NO_HISTORY_PROMPT_TEMPLATE,
    WELCOME_CHANNEL_IDS, DEFAULT_WELCOME_MESSAGE,
    LEAVE_ALLOWED_ROLES
)
from app.ai_handler import AIHandler
from pydantic import ValidationError
from app.reminder_manager import ReminderManager
from app.welcomed_members_db import WelcomedMembersDB
from app.leave_manager import LeaveManager
from app.ai.agents.leave import agent_leave

# Initialize bot with all intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # 啟用成員相關事件
intents.guilds = True   # 啟用伺服器相關事件
bot = commands.Bot(command_prefix="!", intents=intents)

# Rate limiting
message_timestamps: Dict[int, List[float]] = defaultdict(list)

# Global variables
reminder_manager = None
ai_handler = None
welcomed_members_db = None
leave_manager = None

def check_rate_limit(user_id: int) -> bool:
    """Check if user has exceeded rate limit"""
    current_time = time.time()
    # Remove old timestamps
    message_timestamps[user_id] = [
        ts for ts in message_timestamps[user_id]
        if current_time - ts < RATE_LIMIT_PERIOD
    ]
    
    if len(message_timestamps[user_id]) >= RATE_LIMIT_MESSAGES:
        return False
    
    message_timestamps[user_id].append(current_time)
    return True

def split_message(text: str) -> List[str]:
    """Split a long message into multiple parts at natural break points"""
    if len(text) <= MAX_MESSAGE_LENGTH:
        return [text]
    
    parts = []
    current_part = ""
    
    while text:
        # If remaining text fits in one message
        if len(text) <= MAX_MESSAGE_LENGTH:
            parts.append(current_part + text if current_part else text)
            break
            
        # Find the best split point
        split_index = MAX_MESSAGE_LENGTH
        for split_char in SPLIT_CHARS:
            last_index = text.rfind(split_char, 0, MAX_MESSAGE_LENGTH)
            if last_index != -1:
                split_index = last_index + len(split_char)
                break
                
        # Add the part and continue with remaining text
        part = text[:split_index]
        if current_part:
            part = current_part + part
            current_part = ""
        parts.append(part.strip())
        text = text[split_index:].strip()
        
    return parts

@bot.event
async def on_ready():
    global reminder_manager, ai_handler, welcomed_members_db, leave_manager
    print(f'{bot.user} has connected to Discord!')
    
    # # 註冊斜線命令
    # try:
    #     print("開始註冊斜線命令...")
    #     await bot.tree.sync()
    #     print("斜線命令註冊完成！")
    # except Exception as e:
    #     print(f"註冊斜線命令時發生錯誤: {str(e)}")
        
    # Initialize managers
    reminder_manager = ReminderManager(bot)
    reminder_manager.start()
    leave_manager = LeaveManager()
    ai_handler = AIHandler(reminder_manager, leave_manager, bot)
    welcomed_members_db = WelcomedMembersDB()

    # 啟動請假公告更新器
    print("啟動請假公告更新器...")
    asyncio.create_task(ai_handler.start_leave_announcement_updater())
    print("請假公告更新器已啟動")

    # 啟動歡迎訊息重試機制
    print("啟動歡迎訊息重試機制...")
    asyncio.create_task(retry_welcome_messages())
    print("歡迎訊息重試機制已啟動")

    await bot.change_presence(activity=discord.Game(name=BOT_ACTIVITY))


# 新增成員加入事件處理
@bot.event
async def on_member_join(member):
    print(f"新成員加入事件觸發: {member.name} (ID: {member.id})")
    
    # 確保 AI handler 和歡迎資料庫已初始化
    global ai_handler, welcomed_members_db
    if ai_handler is None:
        print("初始化 AI handler")
        ai_handler = AIHandler(reminder_manager, leave_manager, bot)
    
    if welcomed_members_db is None:
        print("初始化歡迎資料庫")
        welcomed_members_db = WelcomedMembersDB()
    
    # 更新成員加入記錄
    is_first_join, join_count = welcomed_members_db.add_or_update_member(
        member.id, 
        member.guild.id, 
        member.name
    )
    
    print(f"成員 {member.name} 加入狀態 - 首次加入: {is_first_join}, 加入次數: {join_count}")
    
    # 如果是第三次或更多次加入，不發送歡迎訊息
    if join_count > 2:
        print(f"成員 {member.name} 已經加入 {join_count} 次，不再發送歡迎訊息")
        return
    
    # 檢查是否有配置歡迎頻道
    if not WELCOME_CHANNEL_IDS:
        print("警告：未配置歡迎頻道 ID")
        return
        
    print(f"配置的歡迎頻道 IDs: {WELCOME_CHANNEL_IDS}")
        
    # 嘗試在配置的歡迎頻道中發送訊息
    welcome_sent = False
    for channel_id in WELCOME_CHANNEL_IDS:
        try:
            print(f"嘗試在頻道 {channel_id} 發送歡迎訊息")
            channel = bot.get_channel(channel_id)
            
            if not channel:
                print(f"無法獲取頻道 {channel_id}，可能是ID錯誤或機器人沒有權限")
                continue
                
            print(f"成功獲取頻道: {channel.name} (ID: {channel_id})")
            
            # 檢查權限
            permissions = channel.permissions_for(member.guild.me)
            if not permissions.send_messages:
                print(f"機器人在頻道 {channel_id} 沒有發送訊息的權限")
                continue
                
            print(f"機器人在頻道 {channel_id} 具有發送訊息的權限")
            
            # 根據加入次數生成不同的歡迎訊息
            welcome_prompt = f"""有一位{'新的' if is_first_join else '回歸的'}使用者 {member.display_name} {'首次' if is_first_join else '第二次'}加入了我們的伺服器！

作為一個活潑可愛的精靈，請你：
1. 用充滿想像力和創意的方式歡迎他
2. 可以提到他的名字，但要巧妙地融入故事中
3. 可以加入一些奇幻或有趣的元素
4. 用 2-3 句話來表達，不要太短
5. 適當使用表情符號來增添趣味
6. {'歡迎新成員加入並簡單介紹伺服器' if is_first_join else '熱情歡迎老朋友回來'}

請生成一段溫暖但有趣的歡迎訊息。記得要活潑、有趣、富有創意，但不要太過誇張或失禮。"""

            print(f"開始生成歡迎訊息，提示詞: {welcome_prompt}")
            
            try:
                async with channel.typing():
                    response_received = False
                    full_response = ""
                    async for chunk in ai_handler.get_streaming_response(welcome_prompt):
                        if chunk:  # 只在有內容時處理
                            print(f"收到回應片段: {chunk}")
                            full_response += chunk
                            
                    if full_response:
                        print(f"生成的完整歡迎訊息: {full_response}")
                        await channel.send(f"{member.mention} {full_response}")
                        welcome_sent = True
                        response_received = True
                        # 標記歡迎成功
                        welcomed_members_db.mark_welcome_success(member.id, member.guild.id)
                    else:
                        print("AI 沒有生成任何回應")
                        # 標記歡迎失敗
                        welcomed_members_db.mark_welcome_failed(member.id, member.guild.id)
            except discord.Forbidden as e:
                print(f"發送訊息時權限錯誤: {str(e)}")
                welcomed_members_db.mark_welcome_failed(member.id, member.guild.id)
                continue
            except Exception as e:
                print(f"在頻道 {channel_id} 生成/發送歡迎訊息時發生錯誤: {str(e)}")
                welcomed_members_db.mark_welcome_failed(member.id, member.guild.id)
                continue
            
            if welcome_sent:
                print("成功發送歡迎訊息")
                break  # 如果已經成功發送訊息，就不需要嘗試其他頻道
            
        except Exception as e:
            print(f"處理頻道 {channel_id} 時發生錯誤: {str(e)}")
            welcomed_members_db.mark_welcome_failed(member.id, member.guild.id)
            continue
    
    # 如果所有配置的頻道都失敗了，且這是第一次或第二次加入，嘗試找一個可用的文字頻道
    if not welcome_sent:
        print("在配置的頻道中發送訊息失敗，嘗試使用備用頻道")
        try:
            # 尋找第一個可用的文字頻道
            fallback_channel = next((channel for channel in member.guild.channels 
                                   if isinstance(channel, discord.TextChannel) and 
                                   channel.permissions_for(member.guild.me).send_messages), None)
            
            if fallback_channel:
                print(f"找到備用頻道: {fallback_channel.name} (ID: {fallback_channel.id})")
                # 發送預設歡迎訊息
                await fallback_channel.send(DEFAULT_WELCOME_MESSAGE.format(member=member.mention))
                print(f"使用備用頻道 {fallback_channel.id} 發送歡迎訊息成功")
                welcomed_members_db.mark_welcome_success(member.id, member.guild.id)
            else:
                print("找不到任何可用的頻道來發送歡迎訊息")
                welcomed_members_db.mark_welcome_failed(member.id, member.guild.id)
                
        except Exception as e:
            print(f"使用備用頻道發送歡迎訊息時發生錯誤: {str(e)}")
            welcomed_members_db.mark_welcome_failed(member.id, member.guild.id)
    
    print("成員加入事件處理完成")

async def get_chat_history(channel, target_chars=CHAT_HISTORY_TARGET_CHARS, max_messages=CHAT_HISTORY_MAX_MESSAGES):
    """
    Get chat history with dynamic message count based on content length.
    """
    messages = []
    total_chars = 0
    
    try:
        async for msg in channel.history(limit=max_messages):
            # Format message with timestamp
            formatted_msg = f"{msg.author.display_name}: {msg.content}"
            msg_chars = len(formatted_msg)
            
            # If this message would exceed our target, and we already have some messages, stop
            if total_chars + msg_chars > target_chars and messages:
                print(f"已達到目標字符數，停止收集訊息")
                break
                
            print(f"收集到訊息: {formatted_msg}")
            messages.append(formatted_msg)
            total_chars += msg_chars
            
            # If we've collected enough characters, stop
            if total_chars >= target_chars:
                print(f"已達到目標字符數，停止收集訊息")
                break
    except discord.errors.Forbidden:
        print("無法讀取訊息歷史")
        return []
    except Exception as e:
        print(f"讀取訊息歷史時發生錯誤: {str(e)}")
        return []
    
    # Reverse to get chronological order
    messages.reverse()
    
    print(f"已收集 {len(messages)} 條訊息，共 {total_chars} 字符")
    return messages

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Process commands first
    await bot.process_commands(message)
    
    # Check for mentions, but only if the message author is not a bot
    if not message.author.bot:
        for mention in message.mentions:
            # 檢查被提及的用戶是否正在請假
            leave_info = leave_manager.get_active_leave(mention.id, message.guild.id)
            if leave_info:
                await ai_handler.handle_mention_of_leave_user(message, mention, leave_info)
                continue

    # Check if the bot was mentioned
    if bot.user in message.mentions:
        await handle_mention(message)
    # Random reply chance
    elif (len(message.content) >= MIN_MESSAGE_LENGTH and
          not message.content.startswith(IGNORED_PREFIXES) and
          not message.author.bot and
          random.random() < RANDOM_REPLY_CHANCE):
        print(f"觸發隨機回覆，訊息: {message.content}")
        await handle_ai_response(message, is_random=True)

async def handle_mention(message):
    """Handle when bot is mentioned"""
    print(f"Checking rate limit for user {message.author.id}")
    if not check_rate_limit(message.author.id):
        await message.reply(RATE_LIMIT_ERROR)
        return

    # Remove the bot mention and get the actual message
    content = message.content.replace(f'<@{bot.user.id}>', '').strip()
    if not content:
        await message.reply("Hello! How can I help you today?")
        return

    await handle_ai_response(message, content)

async def handle_ai_response(message, content=None, is_random=False):
    """Handle AI response generation and sending"""
    if content is None:
        content = message.content

    context_copy = content

    # Get chat history
    chat_history = await get_chat_history(message.channel)
    if chat_history:
        context = "\n".join(chat_history)
        if is_random:
            full_prompt = RANDOM_PROMPT_TEMPLATE.format(context=context, content=content)
        else:
            full_prompt = HISTORY_PROMPT_TEMPLATE.format(context=context, content=content)
    else:
        if is_random:
            full_prompt = NO_HISTORY_PROMPT_TEMPLATE.format(content=content)
        else:
            full_prompt = content

    async with message.channel.typing():
        response_messages = []
        current_message = await message.reply(BOT_THINKING_MESSAGE if not is_random else BOT_RANDOM_THINKING_MESSAGE)
        response_messages.append(current_message)
        
        # Initialize variables for streaming response
        full_response = ""
        buffer = ""
        last_update = time.time()
        print("--------------------------------")
        print(f"context_copy: {context_copy}")
        print("--------------------------------")
        
        try:
            async for chunk in ai_handler.get_streaming_response(
                full_prompt, 
                context_copy,
                message.author.id,
                message.channel.id,
                message.guild.id
            ):
                # Skip if chunk is already in the full response
                if chunk in full_response:
                    continue
                    
                buffer += chunk
                current_time = time.time()
                
                # Update message more frequently
                if (len(buffer) >= STREAM_MIN_UPDATE_LENGTH or
                    any(char in buffer for char in STREAM_UPDATE_CHARS) or
                    current_time - last_update >= STREAM_UPDATE_INTERVAL):
                    
                    # Add buffer to full response
                    full_response += buffer
                    
                    # Check if we need to split the message
                    if len(full_response) > MAX_MESSAGE_LENGTH:
                        parts = split_message(full_response)
                        
                        # Update or create messages for each part
                        for i, part in enumerate(parts):
                            if i < len(response_messages):
                                if response_messages[i].content != part:
                                    await response_messages[i].edit(content=part)
                            else:
                                new_message = await message.channel.send(part)
                                response_messages.append(new_message)
                    else:
                        await current_message.edit(content=full_response)
                    
                    buffer = ""
                    last_update = current_time
                    await asyncio.sleep(STREAM_UPDATE_INTERVAL)
            
            # Handle any remaining buffer
            if buffer and buffer not in full_response:
                full_response += buffer
                if len(full_response) > MAX_MESSAGE_LENGTH:
                    parts = split_message(full_response)
                    for i, part in enumerate(parts):
                        if i < len(response_messages):
                            if response_messages[i].content != part:
                                await response_messages[i].edit(content=part)
                        else:
                            await message.channel.send(part)
                else:
                    await current_message.edit(content=full_response)

        except ValidationError as e:
            error_msg = f"Sorry, I encountered a validation error: {str(e)}"
            print(error_msg)  # Log the error
            await current_message.edit(content=error_msg)
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            print(error_msg)  # Log the error
            await current_message.edit(content=error_msg)

@bot.event
async def on_error(event, *args, **kwargs):
    print(f'Error in {event}:', flush=True)
    raise

def has_leave_permission(member: discord.Member) -> bool:
    """檢查成員是否擁有請假權限"""
    return any(role.id in LEAVE_ALLOWED_ROLES for role in member.roles)

async def retry_welcome_messages():
    """定期檢查並重試失敗的歡迎訊息"""
    while True:
        try:
            if welcomed_members_db is None:
                await asyncio.sleep(60)
                continue

            pending_welcomes = welcomed_members_db.get_pending_welcomes()
            for welcome in pending_welcomes:
                try:
                    guild = bot.get_guild(welcome['guild_id'])
                    if not guild:
                        print(f"無法找到伺服器 {welcome['guild_id']}")
                        continue

                    member = guild.get_member(welcome['user_id'])
                    if not member:
                        print(f"無法找到成員 {welcome['user_id']}")
                        continue

                    # 重新觸發歡迎流程
                    await on_member_join(member)
                    
                except Exception as e:
                    print(f"重試歡迎訊息時發生錯誤: {str(e)}")

            await asyncio.sleep(300)  # 每5分鐘檢查一次
            
        except Exception as e:
            print(f"重試歡迎訊息時發生錯誤: {str(e)}")
            await asyncio.sleep(300)

def main():
    try:
        bot.run(DISCORD_TOKEN)
    finally:
        # Stop reminder manager
        if reminder_manager:
            reminder_manager.stop()
            
if __name__ == "__main__":
    main() 