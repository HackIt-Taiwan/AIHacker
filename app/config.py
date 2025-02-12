import os
from dotenv import load_dotenv
from typing import List, Tuple

# Load environment variables
load_dotenv()

# Discord Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# AI Service Configuration
PRIMARY_AI_SERVICE = os.getenv('PRIMARY_AI_SERVICE', 'azureopenai')  # Default to Azure OpenAI
PRIMARY_MODEL = os.getenv('PRIMARY_MODEL', 'gpt-4o')  # Default model

CLASSIFIER_AI_SERVICE = os.getenv('CLASSIFIER_AI_SERVICE', 'gemini')  # Default to Gemini
CLASSIFIER_MODEL = os.getenv('CLASSIFIER_MODEL', 'gemini-1.0-pro')  # Default model

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')

# Google Gemini Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Tavily Search Configuration
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
TAVILY_SEARCH_MAX_RESULTS = int(os.getenv('TAVILY_SEARCH_MAX_RESULTS', '5'))

# Bot Configuration
TYPING_INTERVAL = float(os.getenv('TYPING_INTERVAL', '2'))  # seconds
STREAM_CHUNK_SIZE = int(os.getenv('STREAM_CHUNK_SIZE', '20'))  # characters
RESPONSE_TIMEOUT = int(os.getenv('RESPONSE_TIMEOUT', '300'))  # seconds
BOT_ACTIVITY = os.getenv('BOT_ACTIVITY', "人類...")  # Discord bot activity status
BOT_THINKING_MESSAGE = os.getenv('BOT_THINKING_MESSAGE', "沒看過精靈思考嗎？.....")  # Message shown when bot is thinking
BOT_RANDOM_THINKING_MESSAGE = os.getenv('BOT_RANDOM_THINKING_MESSAGE', "✨")  # Message shown when bot is thinking (random trigger)

# Welcome Configuration
WELCOME_CHANNEL_IDS = [int(id.strip()) for id in os.getenv('WELCOME_CHANNEL_IDS', '').split(',') if id.strip()]  # Welcome channel IDs
DEFAULT_WELCOME_MESSAGE = os.getenv('DEFAULT_WELCOME_MESSAGE', "歡迎 {member} 加入我們的伺服器！✨")  # Default welcome message

# Rate Limiting
RATE_LIMIT_MESSAGES = int(os.getenv('RATE_LIMIT_MESSAGES', '6'))  # Maximum messages per period
RATE_LIMIT_PERIOD = int(os.getenv('RATE_LIMIT_PERIOD', '180'))  # seconds
RATE_LIMIT_ERROR = os.getenv('RATE_LIMIT_ERROR', "你發太多訊息了，請稍等一下。")  # Rate limit error message

# Message Handling
MAX_MESSAGE_LENGTH = int(os.getenv('MAX_MESSAGE_LENGTH', '1900'))  # Discord's limit is 2000, leaving some margin
MIN_MESSAGE_LENGTH = int(os.getenv('MIN_MESSAGE_LENGTH', '3'))  # Minimum trigger length
IGNORED_PREFIXES = tuple(os.getenv('IGNORED_PREFIXES', '!,?,/,$,#').split(','))  # Ignored command prefixes
RANDOM_REPLY_CHANCE = float(os.getenv('RANDOM_REPLY_CHANCE', '0.001'))  # 0.1% chance of random reply
STREAM_UPDATE_INTERVAL = float(os.getenv('STREAM_UPDATE_INTERVAL', '0.1'))  # seconds between message updates
STREAM_MIN_UPDATE_LENGTH = int(os.getenv('STREAM_MIN_UPDATE_LENGTH', '5'))  # Minimum characters before updating message
STREAM_UPDATE_CHARS = os.getenv('STREAM_UPDATE_CHARS', '.,!,?\n,，,。,！,？').split(',')  # Characters that trigger update

# Chat History
CHAT_HISTORY_TARGET_CHARS = int(os.getenv('CHAT_HISTORY_TARGET_CHARS', '3000'))  # Target character count
CHAT_HISTORY_MAX_MESSAGES = int(os.getenv('CHAT_HISTORY_MAX_MESSAGES', '300'))  # Maximum message count

# AI Response Configuration
AI_MAX_RETRIES = int(os.getenv('AI_MAX_RETRIES', '5'))  # Maximum retry attempts
AI_RETRY_DELAY = int(os.getenv('AI_RETRY_DELAY', '15'))  # seconds, retry interval
AI_ERROR_MESSAGE = os.getenv('AI_ERROR_MESSAGE', "抱歉，AI 服務暫時無法回應，請稍後再試。")  # Error message when AI fails

# Message Split Configuration
SPLIT_CHARS = os.getenv('SPLIT_CHARS', '\n\n,\n,。,！,？,.,!,?, ').split(',')

# Database Paths
DB_ROOT = os.getenv('DB_ROOT', 'data')  # Root directory for all database files
REMINDER_DB_PATH = os.path.join(DB_ROOT, os.getenv('REMINDER_DB_NAME', 'reminders.db'))
WELCOMED_MEMBERS_DB_PATH = os.path.join(DB_ROOT, os.getenv('WELCOMED_MEMBERS_DB_NAME', 'welcomed_members.db'))
LEAVE_DB_PATH = os.path.join(DB_ROOT, os.getenv('LEAVE_DB_NAME', 'leaves.db'))
INVITE_DB_PATH = os.path.join(DB_ROOT, os.getenv('INVITE_DB_NAME', 'invites.db'))
QUESTION_DB_PATH = os.path.join(DB_ROOT, os.getenv('QUESTION_DB_NAME', 'questions.db'))

# Reminder Configuration
REMINDER_CHECK_INTERVAL = int(os.getenv('REMINDER_CHECK_INTERVAL', '60'))  # Check interval in seconds

# Leave Configuration
LEAVE_ALLOWED_ROLES = [int(id.strip()) for id in os.getenv('LEAVE_ALLOWED_ROLES', '').split(',') if id.strip()]  # Roles allowed to use leave commands
LEAVE_ANNOUNCEMENT_CHANNEL_IDS = [int(id.strip()) for id in os.getenv('LEAVE_ANNOUNCEMENT_CHANNEL_IDS', '').split(',') if id.strip()]  # Leave announcement channel IDs

# Invite Configuration
INVITE_TIME_ZONE = os.getenv('INVITE_TIME_ZONE', 'Asia/Taipei')  # Timezone setting
INVITE_ALLOWED_ROLES = [int(id.strip()) for id in os.getenv('INVITE_ALLOWED_ROLES', '').split(',') if id.strip()]  # Roles allowed to manage invites
INVITE_LIST_PAGE_SIZE = int(os.getenv('INVITE_LIST_PAGE_SIZE', '10'))  # Items per page
INVITE_LIST_MAX_PAGES = int(os.getenv('INVITE_LIST_MAX_PAGES', '5'))  # Maximum number of pages

# Question Channel Configuration
QUESTION_CHANNEL_ID = int(os.getenv('QUESTION_CHANNEL_ID', '0'))  # Question channel ID
QUESTION_RESOLVER_ROLES = [int(id.strip()) for id in os.getenv('QUESTION_RESOLVER_ROLES', '').split(',') if id.strip()]  # Roles allowed to resolve questions
QUESTION_EMOJI = os.getenv('QUESTION_EMOJI', '❓')  # Question emoji
QUESTION_RESOLVED_EMOJI = os.getenv('QUESTION_RESOLVED_EMOJI', '✅')  # Emoji for resolved questions

# Crazy Talk Configuration
CRAZY_TALK_ALLOWED_USERS = [int(id.strip()) for id in os.getenv('CRAZY_TALK_ALLOWED_USERS', '').split(',') if id.strip()]  # Users allowed to use crazy talk

# Notion Configuration
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_FAQ_PAGE_ID = os.getenv('NOTION_FAQ_PAGE_ID')
NOTION_FAQ_CHECK_ENABLED = os.getenv('NOTION_FAQ_CHECK_ENABLED', 'True').lower() == 'true'

# Message Types (for classifier)
MESSAGE_TYPES = {
    'SEARCH': 'search',      # Requires information search
    'CHAT': 'chat',         # General chat
    'REMINDER': 'reminder', # Set reminder
    'LEAVE': 'leave',       # Leave related
    'UNKNOWN': 'unknown'    # Cannot classify
}

# Prompt Templates
HISTORY_PROMPT_TEMPLATE = os.getenv('HISTORY_PROMPT_TEMPLATE', """
以下是聊天室的歷史記錄，按照時間順序由舊到新排列。
最早的訊息在最上面，最新的訊息在最下面：

{context}

-----------------

當前問題：{content}

-----------------

請根據上述對話歷史回答最新的問題。記住：歷史訊息是由舊到新排序，最後一條是最新的訊息。""")

RANDOM_PROMPT_TEMPLATE = os.getenv('RANDOM_PROMPT_TEMPLATE', """
以下是聊天室的歷史記錄，按照時間順序由舊到新排列。
最早的訊息在最上面，最新的訊息在最下面：

{context}

-----------------

有人說了：{content}

-----------------

請以一個活潑的精靈身份，對這句話做出簡短的回應或評論。記住你是個調皮的精靈，喜歡給人驚喜。
""")

NO_HISTORY_PROMPT_TEMPLATE = os.getenv('NO_HISTORY_PROMPT_TEMPLATE', "有人說了：{content}\n\n請以一個活潑的精靈身份，對這句話做出簡短的回應或評論。記住你是個調皮的精靈，喜歡給人驚喜。")
