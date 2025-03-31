# Docker Deployment Guide

This guide provides instructions on how to deploy the AIHacker Discord Bot using Docker.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) installed on your system
- A valid Discord Bot Token and other required API keys

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/AIHacker.git
   cd AIHacker
   ```

2. Create and configure the environment file:
   ```bash
   cp .env.example .env
   ```
   
3. Edit the `.env` file and fill in all the required values:
   - `DISCORD_TOKEN`: Your Discord bot token
   - API keys for OpenAI, Azure OpenAI, Google Gemini, etc.
   - Other configuration options as needed

## Deployment

### Using Docker Compose (Recommended for Local Development)

1. Start the bot:
   ```bash
   docker-compose up -d
   ```

2. Check the logs:
   ```bash
   docker-compose logs -f
   ```

3. Stop the bot:
   ```bash
   docker-compose down
   ```

### For Cloud Environments

For cloud environments, it's recommended to use the environment variables or secrets management system provided by your cloud platform instead of mounting the `.env` file directly.

1. Edit the `docker-compose.yml` file and make the following changes:

   ```yaml
   services:
     discord-bot:
       # ...other settings...
       volumes:
         - ./data:/app/data
         - ./logs:/app/logs
         # Comment out this line:
         # - ./.env:/app/.env
       # Comment out env_file if using cloud environment variables
       # env_file:
       #   - ./.env
       environment:
         - TZ=Asia/Taipei
         - DISCORD_TOKEN=${DISCORD_TOKEN}
         - PRIMARY_AI_SERVICE=${PRIMARY_AI_SERVICE}
         - PRIMARY_MODEL=${PRIMARY_MODEL}
         # Add other environment variables as needed
   ```

2. Deploy using your cloud provider's deployment tools, making sure to set up the required environment variables or secrets.

#### Using Docker Swarm / Kubernetes

For orchestration platforms, you can use secrets and configs:

```yaml
# Example Docker Swarm stack.yml
version: '3.8'

services:
  discord-bot:
    image: your-registry/aihacker-discord-bot:latest
    volumes:
      - bot_data:/app/data
      - bot_logs:/app/logs
    environment:
      - TZ=Asia/Taipei
    secrets:
      - discord_token
      - azure_openai_key
      - gemini_api_key
    # Configure your secrets as needed

secrets:
  discord_token:
    external: true
  azure_openai_key:
    external: true
  gemini_api_key:
    external: true

volumes:
  bot_data:
  bot_logs:
```

### Using Docker Directly

1. Build the Docker image:
   ```bash
   docker build -t aihacker-discord-bot .
   ```

2. Run the container:
   ```bash
   # For local development with .env file
   docker run -d \
     --name aihacker-discord-bot \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/logs:/app/logs \
     --env-file ./.env \
     --restart unless-stopped \
     aihacker-discord-bot
     
   # For cloud environments with direct environment variables
   docker run -d \
     --name aihacker-discord-bot \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/logs:/app/logs \
     -e DISCORD_TOKEN=your_token_here \
     -e PRIMARY_AI_SERVICE=azureopenai \
     -e PRIMARY_MODEL=gpt-4o \
     -e AZURE_OPENAI_API_KEY=your_key_here \
     -e AZURE_OPENAI_ENDPOINT=your_endpoint_here \
     --restart unless-stopped \
     aihacker-discord-bot
   ```

3. Check the logs:
   ```bash
   docker logs -f aihacker-discord-bot
   ```

## Data Persistence

The Docker configuration includes mounted volumes for data persistence:

- `./data:/app/data`: Stores all persistent data like databases
- `./logs:/app/logs`: Stores log files

This ensures that your data is preserved even if the container is recreated or updated.

## Environment Variables

The bot requires several environment variables. These can be provided in different ways:

1. **Development**: Using a `.env` file with the `env_file` directive
2. **Production**: Using environment variables passed directly to the container
3. **Cloud**: Using secrets management provided by cloud platforms

Some critical environment variables include:

- `DISCORD_TOKEN`: Your Discord bot token
- `PRIMARY_AI_SERVICE`: AI service provider (e.g., "azureopenai")
- `PRIMARY_MODEL`: AI model to use (e.g., "gpt-4o")
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL
- `GEMINI_API_KEY`: Google Gemini API key

## Updating the Bot

To update the bot to a new version:

1. Pull the latest code:
   ```bash
   git pull
   ```

2. Rebuild and restart the container:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

## Troubleshooting

### Connection Issues

If the bot can't connect to Discord:

1. Check the logs:
   ```bash
   docker-compose logs -f
   ```

2. Verify that your environment variables are correctly set, especially `DISCORD_TOKEN`

3. Check Discord's [status page](https://discordstatus.com/) for any outages

### Permission Issues

If you see permission errors in the logs:

1. Make sure the required directories exist:
   ```bash
   mkdir -p data logs
   ```

2. Check permissions of these directories:
   ```bash
   chmod -R 777 data logs
   ```

## Advanced Configuration

### Custom Timezone

The default timezone is set to `Asia/Taipei` in the Docker Compose file. You can change it by editing the `TZ` environment variable.

### Restart Policy

The container is configured to restart automatically unless explicitly stopped. You can change this by modifying the `restart` option. 