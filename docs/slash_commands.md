# Slash Commands

This document explains how slash commands work in our Discord bot and how they are synchronized with Discord.

## Overview

Slash commands (also known as application commands) are commands that appear when a user types `/` in a Discord channel. These commands provide a user-friendly interface for interacting with the bot.

## Available Slash Commands

Our bot currently provides the following slash commands:

- `/create_invite`: Creates a permanent invite link
  - Parameters: `name` (name for the invite)

- `/list_invites`: Lists all invite links with usage statistics
  - Parameters: `page` (optional, defaults to 1)

- `/delete_invite`: Deletes an invite link
  - Parameters: `invite_code` (the code of the invite to delete)

## Command Synchronization

The bot automatically synchronizes all slash commands with Discord when it starts up. This ensures that all commands are available to users and reflect the latest changes.

### How Synchronization Works

When the bot starts and connects to Discord, it:

1. Loads all defined slash commands
2. Sends these commands to Discord's API for registration
3. Reports the number of successfully synced commands in the console logs

This process happens automatically during the bot's initialization phase, so there's no need for manual synchronization after making changes to commands.

## Adding New Slash Commands

To add a new slash command:

1. Define the command using the `@bot.tree.command()` decorator
2. Restart the bot to synchronize the new command

Example:
```python
@bot.tree.command(name="command_name", description="Command description")
async def command_function(interaction: discord.Interaction, parameter: type):
    # Command implementation
    await interaction.response.send_message("Response")
```

## Command Permissions

Slash commands can have permission requirements. These are defined in the command implementation by checking the user's roles or permissions before executing the command.

## Troubleshooting

If slash commands are not working:

1. Check that the bot has the necessary permissions in the server
2. Verify that the commands were successfully synced during startup
3. Make sure the bot has the `applications.commands` scope enabled in its OAuth2 configuration 