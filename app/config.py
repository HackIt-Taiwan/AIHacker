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
TYPING_INTERVAL = 2  # seconds
STREAM_CHUNK_SIZE = 20  # characters
RESPONSE_TIMEOUT = 300  # seconds
BOT_ACTIVITY = "人類..."  # Discord bot activity status
BOT_THINKING_MESSAGE = "沒看過精靈思考嗎？....."  # Message shown when bot is thinking
BOT_RANDOM_THINKING_MESSAGE = "✨"  # Message shown when bot is thinking (random trigger)

# Welcome Configuration
WELCOME_CHANNEL_IDS = [int(id.strip()) for id in os.getenv('WELCOME_CHANNEL_IDS', '').split(',') if id.strip()]  # 歡迎頻道 ID 列表
DEFAULT_WELCOME_MESSAGE = "歡迎 {member} 加入我們的伺服器！✨"  # 預設歡迎訊息

# Rate Limiting
RATE_LIMIT_MESSAGES = 5  # Maximum messages per period
RATE_LIMIT_PERIOD = 60  # seconds
RATE_LIMIT_ERROR = "你發太多訊息了，請稍等一下。"  # Rate limit error message

# Message Handling
MAX_MESSAGE_LENGTH = 1900  # Discord's limit is 2000, leaving some margin
MIN_MESSAGE_LENGTH = 3  # 最短觸發長度
IGNORED_PREFIXES = ('!', '?', '/', '$', '#')  # 忽略的命令前綴
RANDOM_REPLY_CHANCE = 0.005  # 0.5% 機率自動回覆
STREAM_UPDATE_INTERVAL = 0.1  # seconds between message updates
STREAM_MIN_UPDATE_LENGTH = 5  # Minimum characters before updating message
STREAM_UPDATE_CHARS = ['.', '!', '?', '\n', '，', '。', '！', '？']  # Characters that trigger update

# Chat History
CHAT_HISTORY_TARGET_CHARS = 3000  # 目標字符數
CHAT_HISTORY_MAX_MESSAGES = 300  # 最大消息數量

# AI Response Configuration
AI_MAX_RETRIES = 3  # 最大重試次數
AI_RETRY_DELAY = 1  # seconds, 重試間隔
AI_ERROR_MESSAGE = "抱歉，AI 服務暫時無法回應，請稍後再試。"  # Error message when AI fails

# Message Split Configuration
SPLIT_CHARS: List[str] = ['\n\n', '\n', '。', '！', '？', '.', '!', '?', ' ']

# Prompt Templates
HISTORY_PROMPT_TEMPLATE = """
以下是聊天室的歷史記錄，按照時間順序由舊到新排列。
最早的訊息在最上面，最新的訊息在最下面：

{context}

-----------------

當前問題：{content}

-----------------

請根據上述對話歷史回答最新的問題。記住：歷史訊息是由舊到新排序，最後一條是最新的訊息。"""

RANDOM_PROMPT_TEMPLATE = """
以下是聊天室的歷史記錄，按照時間順序由舊到新排列。
最早的訊息在最上面，最新的訊息在最下面：

{context}

-----------------

有人說了：{content}

-----------------

請以一個活潑的精靈身份，對這句話做出簡短的回應或評論。記住你是個調皮的精靈，喜歡給人驚喜。
"""

NO_HISTORY_PROMPT_TEMPLATE = "有人說了：{content}\n\n請以一個活潑的精靈身份，對這句話做出簡短的回應或評論。記住你是個調皮的精靈，喜歡給人驚喜。"

# Message Types (for classifier)
MESSAGE_TYPES = {
    'SEARCH': 'search',      # 需要搜尋資訊
    'CHAT': 'chat',         # 一般閒聊
    'REMINDER': 'reminder', # 設定提醒
    'LEAVE': 'leave',       # 請假相關
    'UNKNOWN': 'unknown'    # 無法分類
}

# Reminder Configuration
REMINDER_CHECK_INTERVAL = 60  # 檢查提醒的間隔（秒）
REMINDER_DB_PATH = "data/reminders.db"  # 提醒資料庫路徑
WELCOMED_MEMBERS_DB_PATH = "data/welcomed_members.db"  # 已歡迎成員資料庫路徑

# Leave Configuration
LEAVE_DB_PATH = "data/leaves.db"  # 請假資料庫路徑
LEAVE_ALLOWED_ROLES = [1234567890]  # 允許使用請假指令的身份組 ID 列表
LEAVE_ANNOUNCEMENT_CHANNEL_IDS = [1234567890]  # 請假公告頻道 ID 列表
