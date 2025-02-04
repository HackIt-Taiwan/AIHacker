"""
Reminder manager for handling reminders.
"""
import os
import sqlite3
import asyncio
from datetime import datetime
import re
from typing import Optional, Tuple, List, Dict
import discord
from app.config import REMINDER_DB_PATH, REMINDER_CHECK_INTERVAL

class ReminderManager:
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self._ensure_db()
        self._task = None

    def _ensure_db(self):
        """Ensure the database exists and has the correct schema."""
        os.makedirs(os.path.dirname(REMINDER_DB_PATH), exist_ok=True)
        
        with sqlite3.connect(REMINDER_DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    reminder_time DATETIME NOT NULL,
                    task TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def parse_reminder(self, content: str) -> Optional[Tuple[str, str, str]]:
        """Parse reminder commands from AI response.
        Returns:
            Tuple of (command_type, time_str, task) or None if no valid command found
            command_type can be 'add', 'list', or 'delete'
        """
        # Check for reminder addition
        add_match = re.search(r'\[REMINDER\]\s*TIME=(.*?)\s*TASK=(.*?)\s*\[/REMINDER\]', 
                            content, re.DOTALL)
        if add_match:
            return ('add', add_match.group(1).strip(), add_match.group(2).strip())
            
        # Check for reminder listing
        list_match = re.search(r'\[LIST_REMINDERS\]\s*\[/LIST_REMINDERS\]', 
                             content, re.DOTALL)
        if list_match:
            return ('list', '', '')
            
        # Check for reminder deletion
        delete_match = re.search(r'\[DELETE_REMINDER\]\s*TASK=(.*?)\s*\[/DELETE_REMINDER\]', 
                               content, re.DOTALL)
        if delete_match:
            return ('delete', '', delete_match.group(1).strip())
            
        return None

    def add_reminder(self, user_id: int, channel_id: int, guild_id: int, 
                    reminder_time: datetime, task: str):
        """Add a new reminder to the database."""
        with sqlite3.connect(REMINDER_DB_PATH) as conn:
            conn.execute('''
                INSERT INTO reminders (user_id, channel_id, guild_id, reminder_time, task)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, channel_id, guild_id, reminder_time.strftime('%Y-%m-%d %H:%M:%S'), task))
            conn.commit()

    def get_user_reminders(self, user_id: int, guild_id: int) -> List[Dict]:
        """Get all reminders for a specific user in a guild."""
        with sqlite3.connect(REMINDER_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT id, reminder_time, task
                FROM reminders
                WHERE user_id = ? AND guild_id = ?
                ORDER BY reminder_time ASC
            ''', (user_id, guild_id))
            
            reminders = []
            for row in cursor:
                reminder_time = datetime.strptime(row['reminder_time'], '%Y-%m-%d %H:%M:%S')
                reminders.append({
                    'id': row['id'],
                    'time': reminder_time,
                    'task': row['task']
                })
            
            return reminders

    def delete_reminder(self, user_id: int, guild_id: int, task: str) -> bool:
        """Delete a reminder for a specific user in a guild by task description.
        Returns True if a reminder was deleted, False otherwise.
        """
        with sqlite3.connect(REMINDER_DB_PATH) as conn:
            cursor = conn.execute('''
                DELETE FROM reminders
                WHERE user_id = ? AND guild_id = ? AND task LIKE ?
            ''', (user_id, guild_id, f'%{task}%'))
            conn.commit()
            return cursor.rowcount > 0

    async def check_reminders(self):
        """Check for due reminders and send notifications."""
        while True:
            try:
                current_time = datetime.now()
                with sqlite3.connect(REMINDER_DB_PATH) as conn:
                    # 獲取到期的提醒
                    cursor = conn.execute('''
                        SELECT id, user_id, channel_id, guild_id, task
                        FROM reminders
                        WHERE reminder_time <= ?
                    ''', (current_time.strftime('%Y-%m-%d %H:%M:%S'),))
                    
                    due_reminders = cursor.fetchall()
                    
                    for reminder in due_reminders:
                        reminder_id, user_id, channel_id, guild_id, task = reminder
                        
                        try:
                            # 獲取頻道並發送提醒
                            channel = self.bot.get_channel(channel_id)
                            if channel:
                                await channel.send(
                                    f"<@{user_id}> 提醒您：{task}"
                                )
                            
                            # 刪除已處理的提醒
                            conn.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))
                            conn.commit()
                            
                        except Exception as e:
                            print(f"Error sending reminder: {str(e)}")
                
            except Exception as e:
                print(f"Error checking reminders: {str(e)}")
            
            await asyncio.sleep(REMINDER_CHECK_INTERVAL)

    def start(self):
        """Start the reminder checking loop."""
        if self._task is None:
            self._task = asyncio.create_task(self.check_reminders())

    def stop(self):
        """Stop the reminder checking loop."""
        if self._task is not None:
            self._task.cancel()
            self._task = None 