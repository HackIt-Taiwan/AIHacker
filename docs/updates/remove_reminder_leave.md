# Reminder and Leave Functionality Removal

## Overview

This update removes the reminder and leave request functionality from the Discord bot. These features allowed users to set reminders and manage leave requests, but they have been completely removed in this update to simplify the bot functionality.

## Changes Made

### Removed Files
- `app/reminder_manager.py` - Managed reminder functionality
- `app/leave_manager.py` - Managed leave request functionality

### Updated Files
- `main.py` - Removed all references to reminder and leave functionality
- `app/ai_handler.py` - Removed reminder and leave handling code
- `app/config.py` - Removed configuration settings for reminders and leave
- `app/ai/ai_select.py` - Removed agent creation for reminder and leave handlers
- `.env` - Removed environment variables for leave configuration
- `.env.example` - Removed example environment variables for leave configuration

### Configuration Updates
- Removed `REMINDER_DB_PATH` and `LEAVE_DB_PATH` from database paths
- Removed `REMINDER_CHECK_INTERVAL` setting
- Removed `LEAVE_ALLOWED_ROLES` and `LEAVE_ANNOUNCEMENT_CHANNEL_IDS` settings
- Removed `REMINDER` and `LEAVE` message types from classifier

## API Changes

### Removed API Endpoints
No explicit API endpoints were removed, but the following command patterns handled by the AI will no longer work:

- `[REMINDER]...[/REMINDER]` - For setting reminders
- `[LIST_REMINDERS]...[/LIST_REMINDERS]` - For listing reminders
- `[DELETE_REMINDER]...[/DELETE_REMINDER]` - For deleting reminders
- `[LEAVE]...[/LEAVE]` - For requesting leave
- `[LIST_LEAVES]...[/LIST_LEAVES]` - For listing leave requests
- `[DELETE_LEAVE]...[/DELETE_LEAVE]` - For deleting leave requests

### AI Response Changes

The AI will no longer process or respond to reminder or leave related commands. Any such commands in user messages will be ignored. The AI response processing has been simplified to focus on general queries only.

## Migration Guide

There is no migration path for users who were using the reminder or leave functionality. Users are advised to use alternative reminder tools or leave tracking systems. The bot will no longer be able to:

1. Set or manage reminders
2. Process or track leave requests
3. Send notifications about upcoming reminders
4. Send leave announcements
5. Create threads for leave discussions

## Technical Implementation Notes

- All database records related to reminders and leave requests stored in the removed database files will be lost
- The background task that checked for due reminders has been removed
- Leave announcement channels will no longer receive leave-related notifications

For any questions or issues related to this change, please contact the development team. 