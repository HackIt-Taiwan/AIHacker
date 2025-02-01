# Discord AI Chat Bot

This Discord bot responds to mentions with AI-generated responses using OpenAI's API. The bot provides streaming responses for a more interactive experience.

## Features
- Responds to @mentions
- Streams responses in real-time
- Uses OpenAI's GPT model
- Configurable settings

## Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your credentials:
```
DISCORD_TOKEN=your_discord_token
OPENAI_API_KEY=your_openai_api_key
```

3. Run the bot:
```bash
python main.py
```

## Configuration
You can modify the bot's behavior in `config.py`:
- Model selection
- Response settings
- Rate limiting

## Requirements
- Python 3.8+
- Discord.py
- OpenAI Python client
- python-dotenv 