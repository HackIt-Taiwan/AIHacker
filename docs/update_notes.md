# Update Notes: Bot Slash Command Synchronization and Bug Fixes

## Overview

This update adds automatic synchronization of slash commands during bot startup and fixes two critical bugs related to datetime comparisons and initialization order.

## Changes

### API and Backend Changes

1. **Automatic Command Synchronization**
   - Added code in the `on_ready` event to sync slash commands with Discord
   - Bot now logs the number of successfully synced commands during startup

2. **Bug Fixes**
   - Fixed timezone comparison error in FAQ processing by ensuring both datetime objects are timezone-aware
   - Fixed initialization order issue by initializing the leave manager before the AI handler
   - Added safety check in leave announcement updater to prevent errors when leave manager is not initialized

### Documentation Updates

1. **New Documentation**
   - Added new documentation in `docs/slash_commands.md` detailing available slash commands and how synchronization works
   
2. **README Updates**
   - Added "自動同步斜線命令（Slash Commands）" to the features list in the README

## Implementation Details

No changes to API endpoints or request/response formats were made. This update focuses on improving the bot's startup process by ensuring that all slash commands are properly registered with Discord and fixing critical bugs.

## How to Use

No action is required from users or developers. The bot will automatically sync slash commands when it starts up.

To verify that commands are properly synced:

1. Check the bot's startup logs for the message "Synced X command(s)"
2. Verify that slash commands are available in the Discord client by typing "/"

## Additional Notes

If you're developing new slash commands, they will be automatically synced when the bot restarts. There's no need for manual command registration. 