import discord
from discord.ext import commands
import asyncio
from collections import defaultdict
import time
from typing import Dict, List

from app.config import (
    DISCORD_TOKEN, TYPING_INTERVAL, STREAM_CHUNK_SIZE,
    RATE_LIMIT_MESSAGES, RATE_LIMIT_PERIOD
)
from app.ai_handler import AIHandler
from pydantic import ValidationError

# Initialize bot with all intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Rate limiting
message_timestamps: Dict[int, List[float]] = defaultdict(list)

# Constants for message splitting
MAX_MESSAGE_LENGTH = 1900  # Discord's limit is 2000, leaving some margin
SPLIT_CHARS = ['\n\n', '\n', '。', '！', '？', '.', '!', '?', ' ']

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
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Game(name="AI Assistant"))

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Check if the bot was mentioned
    if bot.user in message.mentions:
        # Check rate limit
        print(f"Checking rate limit for user {message.author.id}")
        if not check_rate_limit(message.author.id):
            await message.reply("You're sending too many requests. Please wait a moment.")
            return

        # Remove the bot mention and get the actual message
        content = message.content.replace(f'<@{bot.user.id}>', '').strip()
        if not content:
            await message.reply("Hello! How can I help you today?")
            return

        async with message.channel.typing():
            ai_handler = AIHandler()
            response_messages = []
            current_message = await message.reply("沒看過精靈思考嗎？...")
            response_messages.append(current_message)
            
            # Initialize variables for streaming response
            full_response = ""  # Track the complete response
            buffer = ""
            last_update = time.time()
            
            try:
                async for chunk in ai_handler.get_streaming_response(content):
                    # Skip if chunk is already in the full response
                    if chunk in full_response:
                        continue
                        
                    buffer += chunk
                    current_time = time.time()
                    
                    # Update message more frequently
                    if (len(buffer) >= 5 or
                        any(char in buffer for char in ['.', '!', '?', '\n', '，', '。', '！', '？']) or
                        current_time - last_update >= 0.5):
                        
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
                        await asyncio.sleep(0.1)
                
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

    await bot.process_commands(message)

@bot.event
async def on_error(event, *args, **kwargs):
    print(f'Error in {event}:', flush=True)
    raise

def main():
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main() 