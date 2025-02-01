import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Discord Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# AI Service Configuration
AI_SERVICE = os.getenv('AI_SERVICE', 'azureopenai')  # Default to Azure OpenAI
MODEL_USE = os.getenv('MODEL_USE', 'gpt-4')  # Default model

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')

# Google Gemini Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Bot Configuration
TYPING_INTERVAL = 2  # seconds
STREAM_CHUNK_SIZE = 20  # characters
RESPONSE_TIMEOUT = 300  # seconds

# Rate Limiting
RATE_LIMIT_MESSAGES = 5
RATE_LIMIT_PERIOD = 60  # seconds 