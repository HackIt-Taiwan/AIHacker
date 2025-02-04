import discord
from discord.ext import commands
import asyncio
from collections import defaultdict
import time
import random
from typing import Dict, List

from app.config import (
    DISCORD_TOKEN, TYPING_INTERVAL, STREAM_CHUNK_SIZE,
    RATE_LIMIT_MESSAGES, RATE_LIMIT_PERIOD, RATE_LIMIT_ERROR,
    MAX_MESSAGE_LENGTH, MIN_MESSAGE_LENGTH, IGNORED_PREFIXES,
    RANDOM_REPLY_CHANCE, STREAM_UPDATE_INTERVAL, STREAM_MIN_UPDATE_LENGTH,
    STREAM_UPDATE_CHARS, SPLIT_CHARS, BOT_ACTIVITY, BOT_THINKING_MESSAGE,
    BOT_RANDOM_THINKING_MESSAGE, CHAT_HISTORY_TARGET_CHARS,
    CHAT_HISTORY_MAX_MESSAGES, HISTORY_PROMPT_TEMPLATE,
    RANDOM_PROMPT_TEMPLATE, NO_HISTORY_PROMPT_TEMPLATE
)
from app.ai_handler import AIHandler
from pydantic import ValidationError
from app.reminder_manager import ReminderManager

# Initialize bot with all intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Rate limiting
message_timestamps: Dict[int, List[float]] = defaultdict(list)

# Global variables
reminder_manager = None
ai_handler = None

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
    global reminder_manager, ai_handler
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Game(name=BOT_ACTIVITY))
    
    # Initialize reminder manager
    reminder_manager = ReminderManager(bot)
    reminder_manager.start()
    
    # Initialize AI handler
    ai_handler = AIHandler(reminder_manager)

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

    # Check if the bot was mentioned
    if bot.user in message.mentions:
        await handle_mention(message)
    # Random reply chance
    elif (len(message.content) >= MIN_MESSAGE_LENGTH and  # 訊息夠長
          not message.content.startswith(IGNORED_PREFIXES) and  # 不是命令
          not message.author.bot and  # 不是機器人
          random.random() < RANDOM_REPLY_CHANCE):  # 隨機觸發
        
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

def main():
    try:
        bot.run(DISCORD_TOKEN)
    finally:
        # Stop reminder manager
        if reminder_manager:
            reminder_manager.stop()
            
if __name__ == "__main__":
    main() 