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

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

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
WELCOMED_MEMBERS_DB_PATH = os.path.join(DB_ROOT, os.getenv('WELCOMED_MEMBERS_DB_NAME', 'welcomed_members.db'))
INVITE_DB_PATH = os.path.join(DB_ROOT, os.getenv('INVITE_DB_NAME', 'invites.db'))
QUESTION_DB_PATH = os.path.join(DB_ROOT, os.getenv('QUESTION_DB_NAME', 'questions.db'))

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
QUESTION_FAQ_FOUND_EMOJI = os.getenv('QUESTION_FAQ_FOUND_EMOJI', '📚')  # Emoji for questions with FAQ match
QUESTION_FAQ_PENDING_EMOJI = os.getenv('QUESTION_FAQ_PENDING_EMOJI', '⏳')  # Emoji for questions pending after FAQ

# Crazy Talk Configuration
CRAZY_TALK_ALLOWED_USERS = [int(id.strip()) for id in os.getenv('CRAZY_TALK_ALLOWED_USERS', '').split(',') if id.strip()]  # Users allowed to use crazy talk

# Notion Configuration
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_FAQ_PAGE_ID = os.getenv('NOTION_FAQ_PAGE_ID')
NOTION_FAQ_CHECK_ENABLED = os.getenv('NOTION_FAQ_CHECK_ENABLED', 'True').lower() == 'true'

# Content Moderation Configuration
CONTENT_MODERATION_ENABLED = os.getenv('CONTENT_MODERATION_ENABLED', 'True').lower() == 'true'
CONTENT_MODERATION_NOTIFICATION_TIMEOUT = int(os.getenv('CONTENT_MODERATION_NOTIFICATION_TIMEOUT', '10'))  # seconds
CONTENT_MODERATION_BYPASS_ROLES = [int(id.strip()) for id in os.getenv('CONTENT_MODERATION_BYPASS_ROLES', '').split(',') if id.strip()]  # Roles that bypass moderation
MUTE_ROLE_NAME = os.getenv('MUTE_ROLE_NAME', 'Muted')  # Name of the role to use for muting users
MUTE_ROLE_ID = int(os.getenv('MUTE_ROLE_ID', '0'))  # ID of the role to use for muting users

# URL Safety Check Configuration
URL_SAFETY_CHECK_ENABLED = os.getenv('URL_SAFETY_CHECK_ENABLED', 'False').lower() == 'true'
URL_SAFETY_CHECK_API = os.getenv('URL_SAFETY_CHECK_API', 'virustotal')  # virustotal or googlesafe
URL_SAFETY_API_KEY = os.getenv('URL_SAFETY_API_KEY', '')
URL_SAFETY_THRESHOLD = float(os.getenv('URL_SAFETY_THRESHOLD', '0.3'))  # 30% score threshold for unsafe
URL_SAFETY_MAX_URLS = int(os.getenv('URL_SAFETY_MAX_URLS', '5'))  # Maximum URLs to check at once

# URL safety check retry settings
URL_SAFETY_MAX_RETRIES = int(os.getenv('URL_SAFETY_MAX_RETRIES', '3'))
URL_SAFETY_RETRY_DELAY = int(os.getenv('URL_SAFETY_RETRY_DELAY', '2'))  # Base delay in seconds (will use exponential backoff)
URL_SAFETY_REQUEST_TIMEOUT = float(os.getenv('URL_SAFETY_REQUEST_TIMEOUT', '5.0'))  # Timeout in seconds

# Known impersonation and phishing domains to explicitly block
URL_SAFETY_IMPERSONATION_DOMAINS = [
    domain.strip() for domain in os.getenv(
        'URL_SAFETY_IMPERSONATION_DOMAINS', 
        'steamcommunuttly,steamcommunity-login,discord-gift,discordnitro,'
        'roblox-free,free-minecraft,nintendo-games,playstation-gift'
    ).split(',') if domain.strip()
]

# Map of threat types to severity levels (0-10)
URL_SAFETY_SEVERITY_LEVELS = {
    'PHISHING': 9,
    'MALWARE': 10, 
    'SCAM': 8,
    'SUSPICIOUS': 5
}

# Moderation Review Configuration
MODERATION_REVIEW_ENABLED = os.getenv('MODERATION_REVIEW_ENABLED', 'True').lower() == 'true'  # Whether to use moderation review
MODERATION_REVIEW_AI_SERVICE = os.getenv('MODERATION_REVIEW_AI_SERVICE', PRIMARY_AI_SERVICE)  # AI service to use for review
MODERATION_REVIEW_MODEL = os.getenv('MODERATION_REVIEW_MODEL', PRIMARY_MODEL)  # Model to use for review
BACKUP_MODERATION_REVIEW_AI_SERVICE = os.getenv('BACKUP_MODERATION_REVIEW_AI_SERVICE', '')  # Backup AI service to use for review
BACKUP_MODERATION_REVIEW_MODEL = os.getenv('BACKUP_MODERATION_REVIEW_MODEL', '')  # Backup model to use for review
MODERATION_REVIEW_CONTEXT_MESSAGES = int(os.getenv('MODERATION_REVIEW_CONTEXT_MESSAGES', '3'))  # Number of previous messages to include as context

# Moderation Queue Configuration
MODERATION_QUEUE_ENABLED = os.getenv('MODERATION_QUEUE_ENABLED', 'True').lower() == 'true'  # 是否啟用審核隊列
MODERATION_QUEUE_MAX_CONCURRENT = int(os.getenv('MODERATION_QUEUE_MAX_CONCURRENT', '3'))  # 最大並發處理數
MODERATION_QUEUE_CHECK_INTERVAL = float(os.getenv('MODERATION_QUEUE_CHECK_INTERVAL', '1.0'))  # 隊列檢查間隔（秒）
MODERATION_QUEUE_RETRY_INTERVAL = float(os.getenv('MODERATION_QUEUE_RETRY_INTERVAL', '5.0'))  # 重試間隔（秒）
MODERATION_QUEUE_MAX_RETRIES = int(os.getenv('MODERATION_QUEUE_MAX_RETRIES', '5'))  # 最大重試次數

# Message Types (for classifier)
MESSAGE_TYPES = {
    'SEARCH': 'search',      # Requires information search
    'CHAT': 'chat',         # General chat
    'GENERAL': 'general',   # General message
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
