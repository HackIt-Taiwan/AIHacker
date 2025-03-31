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

### Using Docker Compose (Recommended)

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

### Using Docker Directly

1. Build the Docker image:
   ```bash
   docker build -t aihacker-discord-bot .
   ```

2. Run the container:
   ```bash
   docker run -d \
     --name aihacker-discord-bot \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/logs:/app/logs \
     -v $(pwd)/.env:/app/.env \
     --restart unless-stopped \
     aihacker-discord-bot
   ```

3. Check the logs:
   ```bash
   docker logs -f aihacker-discord-bot
   ```

## Data Persistence

The Docker configuration includes three mounted volumes:

- `./data:/app/data`: Stores all persistent data like databases
- `./logs:/app/logs`: Stores log files
- `./.env:/app/.env`: Your environment configuration

This ensures that your data is preserved even if the container is recreated or updated.

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

2. Verify that your `.env` file contains the correct `DISCORD_TOKEN`

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

The default timezone is set to `Asia/Taipei` in the Docker Compose file. You can change it by editing the `TZ` environment variable in `docker-compose.yml`.

### Restart Policy

The container is configured to restart automatically unless explicitly stopped. You can change this by modifying the `restart` option in `docker-compose.yml`. 