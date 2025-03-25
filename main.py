import discord
from discord.ext import commands
import asyncio
from collections import defaultdict
import time
import random
from typing import Dict, List, Tuple, Optional, Any, Set
from datetime import datetime, timedelta, timezone
import re
import os
import logging
import string
import traceback
import json
import aiohttp
import sys
import io
from dotenv import load_dotenv

from app.config import (
    DISCORD_TOKEN, PRIMARY_AI_SERVICE, PRIMARY_MODEL,
    MUTE_ROLE_NAME, MUTE_ROLE_ID, TYPING_INTERVAL, STREAM_CHUNK_SIZE, 
    RESPONSE_TIMEOUT, BOT_ACTIVITY, BOT_THINKING_MESSAGE, BOT_RANDOM_THINKING_MESSAGE,
    WELCOME_CHANNEL_IDS, DEFAULT_WELCOME_MESSAGE, RATE_LIMIT_MESSAGES, 
    RATE_LIMIT_PERIOD, RATE_LIMIT_ERROR, MAX_MESSAGE_LENGTH, MIN_MESSAGE_LENGTH,
    IGNORED_PREFIXES, RANDOM_REPLY_CHANCE, STREAM_UPDATE_INTERVAL, 
    STREAM_MIN_UPDATE_LENGTH, STREAM_UPDATE_CHARS, CHAT_HISTORY_TARGET_CHARS,
    CHAT_HISTORY_MAX_MESSAGES, AI_MAX_RETRIES, AI_RETRY_DELAY, AI_ERROR_MESSAGE,
    SPLIT_CHARS, INVITE_TIME_ZONE, INVITE_ALLOWED_ROLES,
    INVITE_LIST_PAGE_SIZE, INVITE_LIST_MAX_PAGES, QUESTION_CHANNEL_ID, 
    QUESTION_RESOLVER_ROLES, QUESTION_EMOJI, QUESTION_RESOLVED_EMOJI,
    QUESTION_FAQ_FOUND_EMOJI, QUESTION_FAQ_PENDING_EMOJI, CRAZY_TALK_ALLOWED_USERS,
    NOTION_API_KEY, NOTION_FAQ_PAGE_ID, NOTION_FAQ_CHECK_ENABLED,
    CONTENT_MODERATION_ENABLED, CONTENT_MODERATION_BYPASS_ROLES,
    CONTENT_MODERATION_NOTIFICATION_TIMEOUT, MUTE_ROLE_NAME, MUTE_ROLE_ID,
    MODERATION_REVIEW_ENABLED, MODERATION_REVIEW_CONTEXT_MESSAGES,
    MODERATION_QUEUE_ENABLED, MODERATION_QUEUE_MAX_CONCURRENT,
    DB_ROOT, WELCOMED_MEMBERS_DB_PATH, INVITE_DB_PATH, QUESTION_DB_PATH,
    HISTORY_PROMPT_TEMPLATE, RANDOM_PROMPT_TEMPLATE, NO_HISTORY_PROMPT_TEMPLATE,
    URL_SAFETY_CHECK_ENABLED
)
from app.ai_handler import AIHandler
from pydantic import ValidationError
from app.welcomed_members_db import WelcomedMembersDB
from app.invite_manager import InviteManager
from app.question_manager import QuestionManager, QuestionView, FAQResponseView
from app.mute_manager import MuteManager

# Configure logger
logger = logging.getLogger(__name__)

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/discord_bot.log', encoding='utf-8', mode='a'),
        logging.StreamHandler()
    ]
)

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Initialize bot with all intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # 啟用成員相關事件
intents.guilds = True   # 啟用伺服器相關事件
bot = commands.Bot(command_prefix="!", intents=intents)

# Rate limiting
message_timestamps: Dict[int, List[float]] = defaultdict(list)

# Global variables
ai_handler = None
welcomed_members_db = None
invite_manager = None
notion_faq = None
mute_manager = None  # Added for mute management
question_manager = None  # Add this line to fix the error

# Dictionary to track users who have been recently punished
# Keys are user IDs, values are expiration timestamps
tracked_violators = {}
# Time window in seconds during which we won't re-punish a user (5 minutes)
VIOLATION_TRACKING_WINDOW = 300

# 設置空的IGNORED_CHANNELS列表，表示不屏蔽任何頻道
IGNORED_CHANNELS = []

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
    """Called when the client is done preparing the data received from Discord."""
    # Create a prominent login notification with detailed information
    login_message = f"""
==========================================================
                BOT LOGIN SUCCESSFUL
==========================================================
Bot Name: {bot.user.name}
Bot ID: {bot.user.id}
Server Count: {len(bot.guilds)}
Login Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
==========================================================
"""
    # Log the login message
    logger.info(login_message)
    print(login_message)
    
    # Set bot status
    if BOT_ACTIVITY:
        await bot.change_presence(activity=discord.Game(name=BOT_ACTIVITY))
    
    # Start background tasks
    global ai_handler, welcomed_members_db, invite_manager, notion_faq, mute_manager, question_manager
    
    # Load welcomed members database
    from app.welcomed_members_db import WelcomedMembersDB
    welcomed_members_db = WelcomedMembersDB()
    
    # Initialize invite manager
    from app.invite_manager import InviteManager
    invite_manager = InviteManager()
    
    # Initialize AI handler
    from app.ai_handler import AIHandler
    ai_handler = AIHandler(bot=bot)
    
    # Initialize question manager if question channel is set
    if QUESTION_CHANNEL_ID:
        from app.question_manager import QuestionManager
        question_manager = QuestionManager(bot)
    
    # Initialize Notion FAQ service if enabled
    if NOTION_FAQ_CHECK_ENABLED and NOTION_API_KEY and NOTION_FAQ_PAGE_ID:
        from app.services.notion_faq import NotionFAQ
        notion_faq = NotionFAQ(NOTION_API_KEY, NOTION_FAQ_PAGE_ID)
        bot.loop.create_task(check_auto_resolve_faqs())
    
    # Initialize mute manager
    from app.mute_manager import MuteManager
    mute_manager = MuteManager(bot)
    
    # Check for expired mutes
    bot.loop.create_task(check_expired_mutes())
    
    # Start the moderation queue if enabled
    if MODERATION_QUEUE_ENABLED:
        from app.services.moderation_queue import start_moderation_queue
        await start_moderation_queue(bot)
    
    # Create necessary directories if they don't exist
    os.makedirs(DB_ROOT, exist_ok=True)
    
    # Initialize the retry welcome messages task
    bot.loop.create_task(retry_welcome_messages())
    
    # Log successful initialization of all components
    ready_message = f"""
==========================================================
                BOT INITIALIZATION COMPLETE
==========================================================
All components initialized successfully
Bot is ready to handle events
Servers connected: {len(bot.guilds)}
==========================================================
"""
    logger.info(ready_message)
    print(ready_message)

async def send_welcome_to_offline_members(last_online):
    print("Checking for members who joined while bot was offline...")
    for guild in bot.guilds:
        async for member in guild.fetch_members():
            if not member.bot and member.joined_at and member.joined_at > last_online:
                # check not welcomed
                if not welcomed_members_db.get_member_join_count(member.id, guild.id) > 0:
                    print(f"Sending welcome to {member} who joined at {member.joined_at}")
                    await send_welcome(member)

# 新增成員加入事件處理
@bot.event
async def on_member_join(member):
    await send_welcome(member)

async def send_welcome(member: discord.Member):
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

以下是一些歡迎訊息的例子：
- 哇！✨ 看看是誰從異次元的彩虹橋上滑下來啦！{member.display_name} 帶著滿身的星光降臨到我們這個充滿歡樂的小宇宙，我已經聞到空氣中瀰漫著新朋友的香氣了！🌈

- 叮咚！🔮 我正在喝下午茶的時候，{member.display_name} 就這樣從我的茶杯裡冒出來了！歡迎來到我們這個瘋狂又溫暖的小天地，這裡有數不清的驚喜等著你去發現呢！🫖✨

- 咦？是誰把魔法星星撒在地上了？原來是 {member.display_name} 順著星光來到我們的秘密基地！讓我們一起在這個充滿創意和歡笑的地方，創造屬於我們的奇幻故事吧！🌟

- 哎呀！我的水晶球顯示，有個叫 {member.display_name} 的旅行者，騎著會飛的獨角獸來到了我們的魔法聚會！在這裡，每個人都是獨特的魔法師，期待看到你的神奇表演！🦄✨

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

    # Process bot commands
    await bot.process_commands(message)
    
    # Check moderation 
    if CONTENT_MODERATION_ENABLED and (not message.author.bot):
        # 使用審核隊列處理消息
        if MODERATION_QUEUE_ENABLED:
            from app.services.moderation_queue import moderation_queue
            await moderate_message_queue(message)
        else:
            await moderate_message(message)

    # Ignore messages with command prefixes, regardless of case
    if message.content and message.content.lower().startswith(IGNORED_PREFIXES):
        return

    # Check if message is in question channel
    if message.channel.id == QUESTION_CHANNEL_ID:
        # Skip processing if user has resolver roles
        if any(role.id in QUESTION_RESOLVER_ROLES for role in message.author.roles):
            return
            
        # Add question emoji
        await message.add_reaction(QUESTION_EMOJI)
        
        # Create question record and thread first
        question_manager = QuestionManager()
        question_id = question_manager.add_question(
            message.channel.id,
            message.id,
            message.author.id,
            message.content
        )
        
        if question_id:
            # Create discussion thread
            thread = await message.create_thread(
                name=f"問題討論：{message.content[:50]}...",
                reason="問題討論串"
            )
            
            # Update question record with thread ID
            question_manager.update_thread(question_id, thread.id)
            
            # Send confirmation message with button
            confirm_msg = await thread.send(
                f"✅ 已收到您的問題！"
            )
            
            # Add permanent button
            view = QuestionView.create_for_question(question_id)
            await confirm_msg.edit(view=view)
            
            # Check FAQ if enabled
            if NOTION_FAQ_CHECK_ENABLED and notion_faq:
                try:
                    matching_faq = await notion_faq.find_matching_faq(message.content)
                    if matching_faq:
                        # Update emoji
                        await message.clear_reactions()
                        await message.add_reaction(QUESTION_FAQ_FOUND_EMOJI)
                        
                        # Create a minimalistic embed for FAQ response
                        embed = discord.Embed(
                            title="智能解答",
                            description=f"**問題：** {matching_faq['question']}\n**答案：** {matching_faq['answer']}",
                            color=discord.Color.from_rgb(240, 240, 240)  
                        )
                        if matching_faq.get("category"):
                            embed.add_field(name="分類", value=f"{matching_faq['category']}", inline=True)
                        if matching_faq.get("tags"):
                            tags = " • ".join(matching_faq['tags'])
                            embed.add_field(name="標籤", value=tags, inline=True)
                        embed.set_footer(text="請選擇下方按鈕告知您是否滿意這個答案")
                        
                        # Record FAQ response
                        question_manager.record_faq_response(question_id)
                        
                        # Create FAQ response view
                        view = FAQResponseView(question_id)
                        
                        # Send FAQ response in thread
                        await thread.send(
                            embed=embed,
                            view=view
                        )
                except Exception as e:
                    print(f"Error checking FAQ: {str(e)}")

    # Skip the rest of the processing if it's a command
    if message.content.startswith('!'):
        return
    
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

@bot.event
async def on_message_edit(before, after):
    # Ignore edits by the bot itself
    if after.author == bot.user:
        return
    
    # If content moderation is enabled, moderate the edited message
    if CONTENT_MODERATION_ENABLED and (not after.author.bot):
        # 使用審核隊列處理編輯後的消息
        if MODERATION_QUEUE_ENABLED:
            from app.services.moderation_queue import moderation_queue
            await moderate_message_queue(after, is_edit=True)
        else:
            await moderate_message(after, is_edit=True)
    
    # If the edited message mentions the bot, update response
    if bot.user.mentioned_in(after) and before.content != after.content:
        await handle_mention(after)

async def handle_mention(message):
    """Handle user mentions to the bot"""
    # Get the content after the bot mention
    # Skip processing if message is too short
    if len(message.content) < MIN_MESSAGE_LENGTH:
        return
    
    # Apply ignored prefixes check
    for prefix in IGNORED_PREFIXES:
        if message.content.startswith(f"<@{bot.user.id}> {prefix}"):
            return
    
    await handle_ai_response(message)

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

@bot.command(name='crazy')
async def crazy_talk(ctx, *, content: str):
    """讓 crazy talk 回答特定問題
    用法：!crazy [提示詞] | [問題]
    例如：!crazy 用中二病的方式回答 | 為什麼天空是藍色的？
    """
    # 檢查是否為允許的用戶
    if ctx.author.id not in CRAZY_TALK_ALLOWED_USERS:
        await ctx.reply("❌ 你沒有權限使用此指令", ephemeral=True)
        return

    # 先刪除用戶的指令訊息（如果有權限的話）
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        # 如果沒有刪除訊息的權限，至少確保指令回應是私密的
        await ctx.reply("我收到你的請求了！", ephemeral=True)
    except Exception as e:
        print(f"刪除訊息時發生錯誤: {str(e)}")
        await ctx.reply("我收到你的請求了！", ephemeral=True)
        
    # 解析提示詞和問題
    parts = content.split('|', 1)
    if len(parts) == 2:
        prompt_guidance, question = parts[0].strip(), parts[1].strip()
        print(f"Crazy talk 指令觸發 - 用戶: {ctx.author.name}, 提示詞: {prompt_guidance}, 問題: {question}")
        
        # 組合完整提示
        style_prompt = f"""請根據以下提示來回答問題：
在保持你瘋狂本質的同時，請用這個風格回答：
{prompt_guidance}

記住：
1. 不要完全改變你的個性，讓這個風格成為你瘋狂回答的一部分
2. 你始終是個瘋狂的精靈，只是暫時玩扮演遊戲
3. 即使模仿這個風格，也要保持你獨特的幽默感和無厘頭特質

問題是：{question}"""
        question_prompt = style_prompt
    else:
        question = content.strip()
        print(f"Crazy talk 指令觸發 - 用戶: {ctx.author.name}, 問題: {question}")
        question_prompt = question
    
    # 獲取聊天歷史
    chat_history = await get_chat_history(ctx.channel)
    if chat_history:
        context = "\n".join(chat_history)
        full_prompt = HISTORY_PROMPT_TEMPLATE.format(context=context, content=question_prompt)
    else:
        full_prompt = question_prompt
    
    # 確保 AI handler 已初始化
    global ai_handler
    if ai_handler is None:
        print("Initializing AI handler")
        ai_handler = AIHandler(reminder_manager, leave_manager, bot)
    
    try:
        async with ctx.typing():
            full_response = ""
            async for chunk in ai_handler.get_streaming_response(
                full_prompt,
                question,  # 保存原始問題作為上下文
                ctx.author.id,
                ctx.channel.id,
                ctx.guild.id
            ):
                if chunk:
                    full_response += chunk
            
            if full_response:
                # 分割長訊息並發送到頻道（公開的）
                parts = split_message(full_response)
                for part in parts:
                    await ctx.channel.send(part)
            else:
                # 錯誤訊息只給指令發送者看到
                await ctx.reply("❌ 無法生成回應", ephemeral=True)
                
    except Exception as e:
        print(f"Crazy talk 回應時發生錯誤: {str(e)}")
        # 錯誤訊息只給指令發送者看到
        await ctx.reply("❌ 處理請求時發生錯誤", ephemeral=True)

@bot.tree.command(name="create_invite", description="創建一個永久邀請連結")
async def create_invite(interaction: discord.Interaction, name: str):
    """創建一個永久邀請連結
    
    參數:
        name: 邀請連結的名稱（用於追蹤統計）
    """
    # 檢查是否有創建邀請的權限
    if not any(role.id in INVITE_ALLOWED_ROLES for role in interaction.user.roles):
        await interaction.response.send_message("❌ 你沒有權限創建邀請連結", ephemeral=True)
        return

    try:
        # 獲取指定的頻道
        channel = bot.get_channel(1292488786206261371)
        if not channel:
            await interaction.response.send_message("❌ 無法找到指定的頻道", ephemeral=True)
            return

        # 創建永久邀請連結
        invite = await channel.create_invite(
            max_age=0,  # 永不過期
            max_uses=0,  # 無使用次數限制
            unique=True  # 每次創建都是新的
        )

        # 記錄到資料庫
        if invite_manager.add_invite(invite.code, name, interaction.user.id, channel.id):
            await interaction.response.send_message(
                f"✅ 已創建永久邀請連結！\n"
                f"名稱：{name}\n"
                f"連結：{invite.url}\n"
                f"創建者：{interaction.user.mention}",
                ephemeral=False
            )
        else:
            await interaction.response.send_message("❌ 無法記錄邀請連結", ephemeral=True)

    except discord.Forbidden:
        await interaction.response.send_message("❌ 機器人沒有創建邀請的權限", ephemeral=True)
    except Exception as e:
        print(f"創建邀請連結時發生錯誤: {str(e)}")
        await interaction.response.send_message("❌ 創建邀請連結時發生錯誤", ephemeral=True)

@bot.tree.command(name="list_invites", description="查看所有邀請連結的使用統計")
async def list_invites(interaction: discord.Interaction, page: int = 1):
    """查看所有邀請連結的使用統計
    
    參數:
        page: 頁碼（從1開始）
    """
    # 檢查是否有查看邀請的權限
    if not any(role.id in INVITE_ALLOWED_ROLES for role in interaction.user.roles):
        await interaction.response.send_message("❌ 你沒有權限查看邀請統計", ephemeral=True)
        return

    try:
        # 獲取伺服器的所有邀請
        guild_invites = await interaction.guild.invites()
        invites, total_pages = invite_manager.get_invites_page(page, [{'code': inv.code, 'uses': inv.uses} for inv in guild_invites])
        
        if not invites:
            await interaction.response.send_message("📊 目前還沒有任何邀請記錄", ephemeral=True)
            return

        # 構建統計訊息
        message = f"📊 邀請連結使用統計（第 {page}/{total_pages} 頁）：\n\n"
        for invite in invites:
            creator = interaction.guild.get_member(invite['creator_id'])
            creator_mention = creator.mention if creator else "未知用戶"
            created_time = invite['created_at'].strftime("%Y-%m-%d %H:%M")
            
            message += (
                f"📎 **{invite['name']}**\n"
                f"連結：discord.gg/{invite['invite_code']}\n"
                f"使用次數：{invite['uses']} 次\n"
                f"創建者：{creator_mention}\n"
                f"創建時間：{created_time}\n"
                f"{'─' * 20}\n"
            )

        # 添加頁碼導航按鈕
        if total_pages > 1:
            message += f"\n使用 `/list_invites page:<頁碼>` 查看其他頁面"

        await interaction.response.send_message(message, ephemeral=True)

    except Exception as e:
        print(f"獲取邀請統計時發生錯誤: {str(e)}")
        await interaction.response.send_message("❌ 獲取邀請統計時發生錯誤", ephemeral=True)

@bot.tree.command(name="delete_invite", description="刪除一個邀請連結")
async def delete_invite(interaction: discord.Interaction, invite_code: str):
    """刪除一個邀請連結
    
    參數:
        invite_code: 邀請連結的代碼（不是完整URL）
    """
    # 檢查是否有刪除邀請的權限
    if not any(role.id in INVITE_ALLOWED_ROLES for role in interaction.user.roles):
        await interaction.response.send_message("❌ 你沒有權限刪除邀請連結", ephemeral=True)
        return

    try:
        # 獲取伺服器的所有邀請
        guild_invites = await interaction.guild.invites()
        invite_data = [{'code': inv.code, 'uses': inv.uses} for inv in guild_invites]
        
        # 嘗試刪除邀請
        if invite_manager.delete_invite(invite_code, interaction.user.id, invite_data):
            # 嘗試刪除 Discord 上的邀請
            for invite in guild_invites:
                if invite.code == invite_code:
                    await invite.delete()
                    break
            
            await interaction.response.send_message(f"✅ 已成功刪除邀請連結：{invite_code}")
        else:
            await interaction.response.send_message("❌ 無法刪除邀請連結，可能是因為你不是創建者", ephemeral=True)

    except discord.NotFound:
        await interaction.response.send_message("❌ 找不到指定的邀請連結", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ 機器人沒有刪除邀請的權限", ephemeral=True)
    except Exception as e:
        print(f"刪除邀請連結時發生錯誤: {str(e)}")
        await interaction.response.send_message("❌ 刪除邀請連結時發生錯誤", ephemeral=True)

async def check_auto_resolve_faqs():
    """Periodically check and auto-resolve FAQ questions"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            question_manager = QuestionManager()
            questions = question_manager.check_and_auto_resolve_faqs()
            
            for question in questions:
                try:
                    # Mark as resolved
                    if question_manager.mark_question_resolved(question['id'], None, resolution_type="faq_auto"):
                        # Update message reaction
                        channel = bot.get_channel(question['channel_id'])
                        if channel:
                            message = await channel.fetch_message(question['message_id'])
                            if message:
                                await message.clear_reactions()
                                await message.add_reaction(QUESTION_RESOLVED_EMOJI)
                            
                            # Send notification in thread
                            thread = bot.get_channel(question['thread_id'])
                            if thread:
                                await thread.send("ℹ️ 此問題已自動標記為已解決（由 FAQ 回答）。如果您仍需協助，請重新發問。")
                except Exception as e:
                    print(f"Error auto-resolving question {question['id']}: {str(e)}")
                    
        except Exception as e:
            print(f"Error in auto-resolve FAQ check: {str(e)}")
        
        await asyncio.sleep(3600)  # Check every hour

async def check_expired_mutes():
    """Periodically check for expired mutes and remove them."""
    await bot.wait_until_ready()
    
    while not bot.is_closed():
        try:
            if mute_manager:
                await mute_manager.check_expired_mutes()
        except Exception as e:
            print(f"Error checking expired mutes: {e}")
        
        # Check every minute
        await asyncio.sleep(60)

async def moderate_message_queue(message, is_edit=False):
    """Add message to moderation queue for processing"""
    if message.author.bot:
        return  # Skip bot messages
    
    # Add to moderation queue
    from app.services.moderation_queue import moderation_queue
    
    # Prepare task data
    task_data = {
        "message": message,
        "is_edit": is_edit
    }
    
    # Add task to the queue
    moderation_queue.add_moderation_task(
        task_func=moderate_message,
        task_data=task_data,
        task_id=f"mod_{message.id}_{int(time.time())}"
    )

async def moderate_message(message, is_edit=False):
    """
    Moderate message content using OpenAI's moderation API.
    If content is flagged, delete the message, notify the user, and apply appropriate muting.
    
    Args:
        message: The Discord message to moderate
        is_edit: Whether this is an edited message
    """
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Skip moderation for messages from users with bypass roles
    if any(role.id in CONTENT_MODERATION_BYPASS_ROLES for role in message.author.roles):
        return
    
    # Get message author and content
    author = message.author
    text = message.content.strip()
    attachments = message.attachments
    action_type = "edited" if is_edit else "sent"
    
    # Skip empty messages
    if not text and not attachments:
            return
    
    # Check for URLs if enabled
    url_check_result = None
    if URL_SAFETY_CHECK_ENABLED and text:
        from app.ai.service.url_safety import URLSafetyChecker
        try:
            url_checker = URLSafetyChecker()
            urls = await url_checker.extract_urls(text)
            
            if urls:
                logger.info(f"Checking {len(urls)} URLs in message from {author.name}")
                is_unsafe, url_results = await url_checker.check_urls(urls)
                
                # Log the detailed results for each URL
                for url, result in url_results.items():
                    is_url_unsafe = result.get('is_unsafe', False)
                    try:
                        if is_url_unsafe:
                            threat_types = result.get('threat_types', [])
                            severity = result.get('severity', 0)
                            redirected_to = result.get('redirected_to', None)
                            reason = result.get('reason', '')
                            
                            # Safe joining of threat types
                            threat_types_text = ""
                            try:
                                threat_types_text = ', '.join(threat_types)
                            except Exception:
                                threat_types_text = "[格式化錯誤]"
                            
                            # Format the log message with appropriate error handling
                            if redirected_to:
                                logger.warning(
                                    f"URL安全檢查結果: {url} → {redirected_to} | 不安全: {is_url_unsafe} | "
                                    f"威脅類型: {threat_types_text} | 嚴重度: {severity}" + 
                                    (f" | 原因: {reason}" if reason else "")
                                )
                            else:
                                logger.warning(
                                    f"URL安全檢查結果: {url} | 不安全: {is_url_unsafe} | "
                                    f"威脅類型: {threat_types_text} | 嚴重度: {severity}" + 
                                    (f" | 原因: {reason}" if reason else "")
                                )
                        else:
                            # 對於安全URL，記錄更簡潔的信息
                            message_text = result.get('message', '安全')
                            logger.info(f"URL安全檢查結果: {url} | 安全 | {message_text}")
                    except Exception as log_error:
                        # Fallback logging if any encoding or formatting errors occur
                        print(f"URL detail logging error: {str(log_error)}")
                        try:
                            logger.info(f"URL安全檢查結果: [URL記錄錯誤] | 狀態: {'不安全' if is_url_unsafe else '安全'}")
                        except:
                            logger.info("URL安全檢查結果記錄失敗")
                
                if is_unsafe:
                    # One or more URLs are unsafe
                    unsafe_urls = [url for url, result in url_results.items() if result.get('is_unsafe')]
                    threat_types = set()
                    max_severity = 0
                    reasons = set()
                    
                    for url, result in url_results.items():
                        if result.get('is_unsafe'):
                            # Collect all threat types
                            url_threats = result.get('threat_types', [])
                            for threat in url_threats:
                                threat_types.add(threat)
                            
                            # Track maximum severity
                            severity = result.get('severity', 0)
                            max_severity = max(max_severity, severity)
                            
                            # Collect reasons if available
                            reason = result.get('reason')
                            if reason:
                                reasons.add(reason)
                    
                    url_check_result = {
                        "is_unsafe": True,
                        "unsafe_urls": unsafe_urls,
                        "threat_types": list(threat_types),
                        "severity": max_severity,
                        "reasons": list(reasons) if reasons else None,
                        "results": url_results
                    }
                    
                    # Safely join reasons and threat types for logging
                    reason_text = ""
                    if reasons:
                        try:
                            reason_text = f" | 原因: {', '.join(reasons)}"
                        except Exception as e:
                            reason_text = " | 原因: [格式化錯誤]"
                            print(f"Reason formatting error: {str(e)}")
                    
                    threat_text = ""
                    if threat_types:
                        try:
                            threat_text = ', '.join(list(threat_types))
                        except Exception as e:
                            threat_text = "[格式化錯誤]"
                            print(f"Threat type formatting error: {str(e)}")
                    
                    # Safe URL count logging
                    try:
                        url_count = len(urls) if urls else 0
                        unsafe_count = len(unsafe_urls) if unsafe_urls else 0
                        logger.warning(
                            f"URL安全檢查摘要: 用戶 {author.name}的訊息中檢測到 "
                            f"{unsafe_count}/{url_count} 個不安全URL | 威脅類型: {threat_text}{reason_text}"
                        )
                    except Exception as log_error:
                        # Fallback for any logging errors
                        print(f"URL safety logging error: {str(log_error)}")
                        logger.warning("URL安全檢查檢測到不安全URL (詳細信息記錄失敗)")
                    
                    # If URL is unsafe, we'll continue with deletion and notification below
                    # after both URL and content checks are complete
                else:
                    logger.info(f"URL安全檢查摘要: 用戶 {author.name}的訊息中的所有URL ({len(urls)}個) 都是安全的")
        except Exception as e:
            logger.error(f"URL安全檢查錯誤: {str(e)}")

    # Initialize the content moderator for text and images
    from app.ai.service.moderation import ContentModerator
    moderator = ContentModerator()
    
    # Collect all content for moderation
    image_urls = []
    
    # Add attachment URLs
    for attachment in attachments:
        if attachment.content_type and attachment.content_type.startswith('image/'):
            image_urls.append(attachment.url)
    
    # Add image URLs from message content
    if text:
        # Extract image URLs from message content
        image_url_pattern = r'https?://[^\s<>"]+?\.(?:png|jpg|jpeg|gif|webp)'
        image_urls.extend(re.findall(image_url_pattern, text, re.IGNORECASE))
    
    # Skip if no content to moderate and no unsafe URLs
    if (not text and not image_urls) and not (url_check_result and url_check_result.get('is_unsafe')):
        return
    
    try:
        # Moderate content (text and images)
        is_flagged, results = await moderator.moderate_content(text, image_urls)
        
        # If either content is flagged or URLs are unsafe, take action
        if is_flagged or (url_check_result and url_check_result.get('is_unsafe')):
            # Save channel and author information before deletion
            channel = message.channel
            guild = message.guild
            
            # Extract violation categories
            violation_categories = []
            
            # Add URL threat types to violation categories if applicable
            if url_check_result and url_check_result.get('is_unsafe'):
                for threat_type in url_check_result.get('threat_types', []):
                    violation_category = threat_type.lower()  # Convert PHISHING to phishing, etc.
                    if violation_category not in violation_categories:
                        violation_categories.append(violation_category)
            
            # Check text violations
            if results.get("text_result") and results["text_result"].get("categories"):
                categories = results["text_result"]["categories"]
                for category, is_violated in categories.items():
                    if is_violated and category not in violation_categories:
                        violation_categories.append(category)
            
            # Check image violations
            for image_result in results.get("image_results", []):
                if image_result.get("result") and image_result["result"].get("categories"):
                    categories = image_result["result"]["categories"]
                    for category, is_violated in categories.items():
                        if is_violated and category not in violation_categories:
                            violation_categories.append(category)
            
            # If review is enabled and this is not a URL safety issue, check if the flagged content is a false positive
            review_result = None
            if MODERATION_REVIEW_ENABLED and text and not (url_check_result and url_check_result.get('is_unsafe')):
                from app.ai.agents.moderation_review import review_flagged_content
                from app.ai.ai_select import create_moderation_review_agent
                
                try:
                    # Get message context (previous messages)
                    context = ""
                    if hasattr(message.channel, 'history'):
                        context_messages = []
                        async for msg in message.channel.history(limit=MODERATION_REVIEW_CONTEXT_MESSAGES + 1):
                            if msg.id != message.id:
                                context_messages.append(f"{msg.author.name}: {msg.content}")
                                if len(context_messages) >= MODERATION_REVIEW_CONTEXT_MESSAGES:
                                    break
                        
                        if context_messages:
                            context = "最近的訊息（從舊到新）：\n" + "\n".join(reversed(context_messages))
                    
                    # Create the moderation review agent
                    review_agent = await create_moderation_review_agent()
                    
                    # 嘗試創建備用審核代理
                    backup_review_agent = None
                    try:
                        from app.ai.ai_select import create_backup_moderation_review_agent
                        backup_review_agent = await create_backup_moderation_review_agent()
                        if backup_review_agent:
                            print(f"[審核系統] 已準備備用審核服務")
                    except Exception as e:
                        print(f"[審核系統] 準備備用審核服務失敗: {e}")
                    
                    # Review the flagged content using OpenAI mod + LLM
                    review_result = await review_flagged_content(
                        agent=review_agent,
                        content=text,
                        violation_categories=violation_categories,
                        context=context,
                        backup_agent=backup_review_agent
                    )
                    
                    print(f"[審核系統] 用戶 {author.name} 的訊息審核結果: {'非違規(誤判)' if not review_result['is_violation'] else '確認違規'}")
                    
                    # If the review agent determined it's a false positive, don't delete or punish
                    if not review_result["is_violation"]:
                        print(f"[審核系統] 誤判原因: {review_result['reason'][:100]}")
                        # 不對誤判做任何處理，直接返回
                        return
                        
                except Exception as review_error:
                    print(f"[審核系統] 執行審核時出錯: {str(review_error)}")
                    # 只根據違規類型數量來決定
                    if len(violation_categories) >= 3:
                        print(f"[審核系統] 評估失敗但檢測到多種違規類型，視為違規")
                        review_result = {
                            "is_violation": True,
                            "reason": f"評估過程出錯，但內容觸發了多種違規類型({', '.join(violation_categories[:3])})，系統判定為違規。",
                            "original_response": f"ERROR: {str(review_error)}"
                        }
                    # 在其他情況下，繼續常規審核流程，無review_result
            
            # Skip review for URL safety issues - unsafe URLs are always violations
            if url_check_result and url_check_result.get('is_unsafe'):
                if not review_result:
                    review_result = {
                        "is_violation": True,
                        "reason": f"訊息包含不安全的連結，這些連結可能含有詐騙、釣魚或惡意軟體內容。",
                        "original_response": "URL_SAFETY_CHECK: Unsafe URLs detected"
                    }
                elif not review_result.get("is_violation"):
                    # Override non-violation review result for unsafe URLs
                    review_result["is_violation"] = True
                    review_result["reason"] = f"訊息包含不安全的連結，這些連結可能含有詐騙、釣魚或惡意軟體內容。原始審核結果: {review_result['reason']}"
                    review_result["original_response"] = "URL_SAFETY_CHECK: Unsafe URLs detected"
            
            # Delete the message (only happens if the review agent confirms it's a violation or review is disabled)
            try:
                # 只有當審核結果確認為真正違規時才刪除消息，否則保留
                if review_result is None or review_result["is_violation"]:
                    await message.delete()
                    print(f"[審核系統] 已刪除標記為違規的{action_type}消息，用戶: {author.name}")
                else:
                    # 如果被判定為誤判，不刪除消息也不通知用戶
                    print(f"[審核系統] 消息被標記但審核確認為誤判，已保留。用戶: {author.name}")
                    return
            except Exception as e:
                print(f"[審核系統] 刪除消息失敗: {str(e)}")
                return
            
            # Check if user was recently punished - if so, just delete the message without additional notification
            current_time = time.time()
            user_id = author.id
            is_recent_violator = False
            
            if user_id in tracked_violators:
                expiry_time = tracked_violators[user_id]
                if current_time < expiry_time:
                    is_recent_violator = True
                    print(f"[審核系統] 用戶 {author.name} 最近已被處罰，僅刪除消息而不重複處罰")
                else:
                    # Expired tracking, remove from dictionary
                    del tracked_violators[user_id]
            
            # If this is a recent violator, just return after deleting the message
            if is_recent_violator:
                return
                
            # Track this user as a recent violator
            tracked_violators[user_id] = current_time + VIOLATION_TRACKING_WINDOW
            
            # IMPORTANT: Apply muting only if content is confirmed as violation
            mute_success = False
            mute_reason = ""
            mute_embed = None
            if mute_manager and (review_result is None or review_result["is_violation"]):
                try:
                    # Add URL safety results if applicable
                    if url_check_result and url_check_result.get('is_unsafe'):
                        # Update the moderation results to include URL safety results
                        if "url_safety" not in results:
                            results["url_safety"] = url_check_result
                    
                    mute_success, mute_reason, mute_embed = await mute_manager.mute_user(
                        user=author,
                        violation_categories=violation_categories,
                        content=text,
                        details=results
                    )
                    print(f"[審核系統] 用戶 {author.name} 禁言狀態: {mute_success}")
                except Exception as mute_error:
                    print(f"[審核系統] 禁言用戶 {author.name} 時出錯: {str(mute_error)}")
            
            # Clean up old entries in tracked_violators
            if len(tracked_violators) > 1000:  # Just to prevent unbounded growth
                current_time = time.time()
                expired_keys = [k for k, v in tracked_violators.items() if v < current_time]
                for k in expired_keys:
                    del tracked_violators[k]
            
            # Create both embeds then send them simultaneously
            try:
                # Channel notification embed
                notification_embed = discord.Embed(
                    title="⚠️ 內容審核通知",
                    description=f"<@{author.id}> 您的訊息已被系統移除，因為它含有違反社群規範的內容。",
                    color=discord.Color.red()
                )
                
                # DM embed
                dm_embed = discord.Embed(
                    title="🛡️ 內容審核通知",
                    description=f"您在 **{guild.name}** 發送的訊息因含有不適當內容而被移除。",
                    color=discord.Color.from_rgb(230, 126, 34)  # Warm orange color
                )
                
                # Add server icon if available
                if guild.icon:
                    dm_embed.set_thumbnail(url=guild.icon.url)
                
                dm_embed.timestamp = datetime.now(timezone.utc)
                
                # Add URL safety information if applicable
                if url_check_result and url_check_result.get('is_unsafe'):
                    unsafe_urls = url_check_result.get('unsafe_urls', [])
                    if unsafe_urls:
                        url_list = "\n".join([f"- {url}" for url in unsafe_urls[:5]])  # Limit to 5 URLs
                        if len(unsafe_urls) > 5:
                            url_list += f"\n- ...以及 {len(unsafe_urls) - 5} 個其他不安全連結"
                            
                        threat_types_map = {
                            'PHISHING': '釣魚網站',
                            'MALWARE': '惡意軟體',
                            'SCAM': '詐騙網站',
                            'SUSPICIOUS': '可疑網站'
                        }
                        
                        threat_descriptions = []
                        for threat in url_check_result.get('threat_types', []):
                            threat_descriptions.append(threat_types_map.get(threat, threat))
                            
                        threat_text = "、".join(threat_descriptions) if threat_descriptions else "不安全連結"
                        
                        dm_embed.add_field(
                            name="⚠️ 不安全連結",
                            value=f"您的訊息包含可能是{threat_text}的連結：\n{url_list}",
                            inline=False
                        )
                
                # Add violation types with emoji indicators and Chinese translations
                if violation_categories:
                    # Map categories to Chinese with emojis (both slash format and underscore format)
                    category_map = {
                        # Underscore format (as returned by API)
                        "harassment": "😡 騷擾內容",
                        "harassment_threatening": "🔪 威脅性騷擾",
                        "hate": "💢 仇恨言論",
                        "hate_threatening": "⚠️ 威脅性仇恨言論",
                        "self_harm": "💔 自我傷害相關內容",
                        "self_harm_intent": "🆘 自我傷害意圖",
                        "self_harm_instructions": "⛔ 自我傷害指導",
                        "sexual": "🔞 性相關內容",
                        "sexual_minors": "🚫 未成年相關性內容",
                        "violence": "👊 暴力內容",
                        "violence_graphic": "🩸 圖像化暴力內容",
                        "illicit": "🚫 不法行為",
                        "illicit_violent": "💣 暴力不法行為",
                        
                        # Slash format (original)
                        "harassment/threatening": "🔪 威脅性騷擾",
                        "hate/threatening": "⚠️ 威脅性仇恨言論",
                        "self-harm": "💔 自我傷害相關內容",
                        "self-harm/intent": "🆘 自我傷害意圖",
                        "self-harm/instructions": "⛔ 自我傷害指導",
                        "sexual/minors": "🚫 未成年相關性內容",
                        "violence/graphic": "🩸 圖像化暴力內容",
                        "illicit/violent": "💣 暴力不法行為",
                        
                        # URL safety categories
                        "phishing": "🎣 釣魚網站",
                        "malware": "🦠 惡意軟體",
                        "scam": "💸 詐騙內容",
                        "suspicious": "❓ 可疑內容",
                    }
                    
                    violation_list = []
                    for category in violation_categories:
                        category_text = category_map.get(category, f"❌ 違規內容: {category}")
                        violation_list.append(category_text)
                    
                    dm_embed.add_field(
                        name="違規類型",
                        value="\n".join(violation_list),
                        inline=False
                    )
                
                # Add channel information
                dm_embed.add_field(
                    name="📝 頻道",
                    value=f"#{channel.name}",
                    inline=True
                )
                
                # Add violation count if available
                if mute_manager:
                    violation_count = mute_manager.db.get_violation_count(author.id, guild.id)
                    dm_embed.add_field(
                        name="🔢 違規次數",
                        value=f"這是您的第 **{violation_count}** 次違規",
                        inline=True
                    )
                
                # Add a divider
                dm_embed.add_field(
                    name="",
                    value="━━━━━━━━━━━━━━━━━━━━━━━",
                    inline=False
                )
                
                # Add the original content that was flagged
                if text:
                    # Truncate text if too long
                    display_text = text if len(text) <= 1000 else text[:997] + "..."
                    dm_embed.add_field(
                        name="📄 訊息內容",
                        value=f"```\n{display_text}\n```",
                        inline=False
                    )
                
                if image_urls:
                    dm_embed.add_field(
                        name="🖼️ 附件",
                        value=f"包含 {len(image_urls)} 張圖片",
                        inline=False
                    )
                
                # Add another divider
                dm_embed.add_field(
                    name="",
                    value="━━━━━━━━━━━━━━━━━━━━━━━━",
                    inline=False
                )
                
                # Add note and resources
                dm_embed.add_field(
                    name="📋 請注意",
                    value="請確保您發送的內容符合社群規範。重複違規可能導致更嚴重的處罰。\n\n如果您對此決定有疑問，請聯繫伺服器工作人員。",
                    inline=False
                )
                
                # Add guidelines link
                dm_embed.add_field(
                    name="📚 社群規範",
                    value=f"請閱讀我們的[社群規範](https://discord.com/channels/{guild.id}/rules)以了解更多資訊。",
                    inline=False
                )
                
                # Send both messages simultaneously
                tasks = []
                tasks.append(channel.send(embed=notification_embed))
                tasks.append(author.send(embed=dm_embed))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Log any DM errors
                if len(results) > 1 and isinstance(results[1], Exception):
                    print(f"Failed to send DM: {str(results[1])}")
                
                # Send mute notification after content moderation notification
                if mute_success and mute_embed:
                    try:
                        await author.send(embed=mute_embed)
                    except Exception as e:
                        print(f"Failed to send mute notification DM: {str(e)}")

                # Extract channel notification for deletion
                if len(results) > 0 and isinstance(results[0], discord.Message):
                    channel_notification = results[0]
                    # Delete the notification after a short delay
                    await asyncio.sleep(CONTENT_MODERATION_NOTIFICATION_TIMEOUT)
                    await channel_notification.delete()
                
            except Exception as e:
                print(f"Failed to send notification messages: {str(e)}")
    except Exception as e:
        print(f"Error in content moderation: {str(e)}")
        # Log the error but don't raise, to avoid interrupting normal bot operation

def main():
    """Main entry point for the Discord bot"""
    try:
        # Ensure required directories exist
        os.makedirs(DB_ROOT, exist_ok=True)
        os.makedirs(os.path.join(DB_ROOT, 'questions'), exist_ok=True)
        os.makedirs(os.path.join(DB_ROOT, 'welcomed_members'), exist_ok=True)
        os.makedirs(os.path.join(DB_ROOT, 'invites'), exist_ok=True)
        
        # Start the bot
        bot.run(DISCORD_TOKEN, log_handler=None)
    except Exception as e:
        logger.critical(f"Failed to start the bot: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 