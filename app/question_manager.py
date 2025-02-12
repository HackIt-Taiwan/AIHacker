"""
Question manager for handling questions and their threads.
Manages the lifecycle of questions including creation, resolution, and button interactions.
"""
import os
import sqlite3
from datetime import datetime
import discord
from discord.ui import Button, View
from typing import Optional, Dict, List
from app.config import (
    QUESTION_DB_PATH, QUESTION_RESOLVER_ROLES,
    QUESTION_EMOJI, QUESTION_RESOLVED_EMOJI
)

class QuestionButton(Button):
    def __init__(self, question_id: int, is_resolved: bool = False):
        # Initialize button with appropriate style based on resolution status
        super().__init__(
            style=discord.ButtonStyle.green if not is_resolved else discord.ButtonStyle.gray,
            label="已完成" if not is_resolved else "已標記完成",
            custom_id=f"resolve_question_{question_id}",
            disabled=is_resolved
        )
        self.question_id = question_id

    async def callback(self, interaction: discord.Interaction):
        # Check if user has permission to resolve questions
        if not any(role.id in QUESTION_RESOLVER_ROLES for role in interaction.user.roles):
            await interaction.response.send_message("❌ 您沒有標記問題解決的權限！", ephemeral=True)
            return

        # Update question status
        question_manager = QuestionManager()
        
        # Get question info for emoji handling
        question = question_manager.get_question(self.question_id)
        if not question:
            await interaction.response.send_message("❌ 找不到此問題！", ephemeral=True)
            return
            
        if question_manager.mark_question_resolved(self.question_id, interaction.user.id):
            # Update button state
            self.style = discord.ButtonStyle.gray
            self.label = "已標記完成"
            self.disabled = True
            
            # Update view in original message
            view = View.from_message(interaction.message)
            view.clear_items()
            view.add_item(self)
            await interaction.message.edit(view=view)
            
            # Handle emojis in original message
            try:
                channel = interaction.guild.get_channel(question['channel_id'])
                if channel:
                    message = await channel.fetch_message(question['message_id'])
                    if message:
                        # Remove all reactions and add resolved emoji
                        await message.clear_reactions()
                        await message.add_reaction(QUESTION_RESOLVED_EMOJI)
            except Exception as e:
                print(f"Error handling emojis: {str(e)}")
            
            # Send resolution message in thread
            await interaction.channel.send(
                f"✅ 本問題已由 {interaction.user.mention} 標記為已解決！"
            )
            
            # Defer interaction response
            await interaction.response.defer()
        else:
            await interaction.response.send_message("❌ 標記問題解決時發生錯誤！", ephemeral=True)

class QuestionView(View):
    def __init__(self, question_id: int = 0):
        # Initialize view with no timeout for permanent buttons
        super().__init__(timeout=None)
        
        # Only add button for specific questions, not for generic views
        if question_id > 0:
            self.add_item(QuestionButton(question_id))

    @staticmethod
    def create_for_question(question_id: int, is_resolved: bool = False) -> 'QuestionView':
        """Create a view for a specific question with its current state"""
        view = QuestionView()
        view.add_item(QuestionButton(question_id, is_resolved))
        return view

class QuestionManager:
    def __init__(self):
        # Ensure database directory exists
        os.makedirs(os.path.dirname(QUESTION_DB_PATH), exist_ok=True)
        self._ensure_db()

    def _ensure_db(self):
        """Ensure database exists with correct schema"""
        with sqlite3.connect(QUESTION_DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    thread_id INTEGER,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    resolved_at DATETIME,
                    resolved_by INTEGER,
                    UNIQUE(channel_id, message_id)
                )
            ''')
            conn.commit()

    def add_question(self, channel_id: int, message_id: int, user_id: int, content: str) -> Optional[int]:
        """Add a new question record and return its ID"""
        try:
            with sqlite3.connect(QUESTION_DB_PATH) as conn:
                cursor = conn.execute('''
                    INSERT INTO questions (channel_id, message_id, user_id, content)
                    VALUES (?, ?, ?, ?)
                ''', (channel_id, message_id, user_id, content))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
        except Exception as e:
            print(f"Error adding question record: {str(e)}")
            return None

    def update_thread(self, question_id: int, thread_id: int) -> bool:
        """Update the thread ID for a question"""
        try:
            with sqlite3.connect(QUESTION_DB_PATH) as conn:
                conn.execute('''
                    UPDATE questions
                    SET thread_id = ?
                    WHERE id = ?
                ''', (thread_id, question_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error updating question thread: {str(e)}")
            return False

    def mark_question_resolved(self, question_id: int, resolver_id: int) -> bool:
        """Mark a question as resolved"""
        try:
            with sqlite3.connect(QUESTION_DB_PATH) as conn:
                conn.execute('''
                    UPDATE questions
                    SET resolved_at = CURRENT_TIMESTAMP,
                        resolved_by = ?
                    WHERE id = ? AND resolved_at IS NULL
                ''', (resolver_id, question_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error marking question as resolved: {str(e)}")
            return False

    def get_question(self, question_id: int) -> Optional[Dict]:
        """Get question information by ID"""
        try:
            with sqlite3.connect(QUESTION_DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT id, channel_id, message_id, thread_id, user_id,
                           content, created_at, resolved_at, resolved_by
                    FROM questions
                    WHERE id = ?
                ''', (question_id,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            print(f"Error getting question info: {str(e)}")
            return None

    def get_unresolved_questions(self) -> List[Dict]:
        """Get all unresolved questions"""
        try:
            with sqlite3.connect(QUESTION_DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT id, channel_id, message_id, thread_id, user_id,
                           content, created_at
                    FROM questions
                    WHERE resolved_at IS NULL
                    ORDER BY created_at ASC
                ''')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting unresolved questions: {str(e)}")
            return []

    def get_all_questions_with_state(self) -> List[Dict]:
        """Get all questions with their resolution state for button registration"""
        try:
            with sqlite3.connect(QUESTION_DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT id, channel_id, message_id, thread_id,
                           resolved_at IS NOT NULL as is_resolved
                    FROM questions
                    ORDER BY created_at DESC
                ''')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting all question states: {str(e)}")
            return [] 