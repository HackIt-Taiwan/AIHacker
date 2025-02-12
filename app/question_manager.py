"""
Question manager for handling questions and their threads.
Manages the lifecycle of questions including creation, resolution, and button interactions.
"""
import os
import sqlite3
from datetime import datetime, timedelta
import discord
from discord.ui import Button, View
from typing import Optional, Dict, List
from app.config import (
    QUESTION_DB_PATH, QUESTION_RESOLVER_ROLES,
    QUESTION_EMOJI, QUESTION_RESOLVED_EMOJI,
    QUESTION_FAQ_FOUND_EMOJI, QUESTION_FAQ_PENDING_EMOJI
)

class FAQResponseButton(Button):
    # 用於追踪正在處理中的按鈕
    _processing_buttons = set()

    def __init__(self, question_id: int, is_resolved: bool, response_type: str):
        # Initialize button with appropriate style based on response type
        super().__init__(
            style=discord.ButtonStyle.green if response_type == "resolved" else discord.ButtonStyle.gray,
            label="問題已解決" if response_type == "resolved" else "仍需協助",
            custom_id=f"faq_response_{question_id}_{response_type}",
            disabled=is_resolved
        )
        self.question_id = question_id
        self.response_type = response_type

    async def callback(self, interaction: discord.Interaction):
        # 檢查按鈕是否正在處理中
        button_id = f"{self.question_id}_{self.response_type}"
        if button_id in self._processing_buttons:
            await interaction.response.send_message("⏳ 請稍候，正在處理您的請求...", ephemeral=True)
            return

        # 將按鈕標記為處理中
        self._processing_buttons.add(button_id)

        try:
            question_manager = QuestionManager()
            question = question_manager.get_question(self.question_id)
            
            if not question:
                await interaction.response.send_message("❌ 找不到此問題！", ephemeral=True)
                return
                
            if interaction.user.id != question['user_id']:
                await interaction.response.send_message("❌ 只有提問者可以回應 FAQ 的幫助程度！", ephemeral=True)
                return

            # 立即回應交互以避免超時
            await interaction.response.defer(ephemeral=True)

            try:
                # 先禁用所有按鈕以防止重複點擊
                view = self.view
                for item in view.children:
                    item.disabled = True
                await interaction.message.edit(view=view)

                if self.response_type == "resolved":
                    # Mark question as resolved by FAQ
                    if question_manager.mark_question_resolved(self.question_id, None, resolution_type="faq"):
                        # Update original message reactions
                        try:
                            channel = interaction.guild.get_channel(question['channel_id'])
                            if channel:
                                message = await channel.fetch_message(question['message_id'])
                                if message:
                                    await message.clear_reactions()
                                    await message.add_reaction(QUESTION_RESOLVED_EMOJI)
                                    
                                    # Find and disable the original question button
                                    async for msg in interaction.channel.history():
                                        if msg.author == interaction.client.user and "已收到您的問題！" in msg.content:
                                            view = discord.ui.View.from_message(msg)
                                            for item in view.children:
                                                item.disabled = True
                                            await msg.edit(view=view)
                                            break
                        except Exception as e:
                            print(f"Error updating reactions or buttons: {str(e)}")
                        
                        await interaction.followup.send("✅ 感謝您的回饋！很高興 FAQ 能夠解決您的問題。", ephemeral=True)
                        await interaction.channel.send("✅ 提問者表示 FAQ 已解決此問題！")
                else:
                    # Mark as needing further assistance
                    question_manager.mark_faq_insufficient(self.question_id)
                    
                    # Update original message reactions
                    try:
                        channel = interaction.guild.get_channel(question['channel_id'])
                        if channel:
                            message = await channel.fetch_message(question['message_id'])
                            if message:
                                await message.clear_reactions()
                                await message.add_reaction(QUESTION_FAQ_PENDING_EMOJI)
                    except Exception as e:
                        print(f"Error updating reactions: {str(e)}")
                    
                    await interaction.followup.send("✅ 感謝您的回饋！我們會盡快為您提供進一步協助。", ephemeral=True)
                    await interaction.channel.send("ℹ️ 提問者表示需要進一步協助，請相關人員協助回答。")
            except Exception as e:
                print(f"Error handling FAQ response: {str(e)}")
                try:
                    await interaction.followup.send("❌ 處理回應時發生錯誤，請稍後再試。", ephemeral=True)
                except Exception:
                    pass
        finally:
            # 無論成功與否，都要移除處理中的標記
            self._processing_buttons.remove(button_id)

class FAQResponseView(View):
    def __init__(self, question_id: int = 0, is_resolved: bool = False):
        super().__init__(timeout=None)  # No timeout for permanent buttons
        if question_id > 0:
            self.add_item(FAQResponseButton(question_id, is_resolved, "resolved"))
            self.add_item(FAQResponseButton(question_id, is_resolved, "need_help"))

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
                    resolution_type TEXT,
                    faq_response_at DATETIME,
                    faq_status TEXT,
                    UNIQUE(channel_id, message_id)
                )
            ''')
            
            # Check if new columns need to be added
            cursor = conn.execute("PRAGMA table_info(questions)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'resolution_type' not in columns:
                conn.execute('ALTER TABLE questions ADD COLUMN resolution_type TEXT')
            if 'faq_response_at' not in columns:
                conn.execute('ALTER TABLE questions ADD COLUMN faq_response_at DATETIME')
            if 'faq_status' not in columns:
                conn.execute('ALTER TABLE questions ADD COLUMN faq_status TEXT')
            
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

    def mark_question_resolved(self, question_id: int, resolver_id: Optional[int] = None, resolution_type: str = "manual") -> bool:
        """Mark a question as resolved"""
        try:
            with sqlite3.connect(QUESTION_DB_PATH) as conn:
                conn.execute('''
                    UPDATE questions
                    SET resolved_at = CURRENT_TIMESTAMP,
                        resolved_by = ?,
                        resolution_type = ?
                    WHERE id = ? AND resolved_at IS NULL
                ''', (resolver_id, resolution_type, question_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error marking question as resolved: {str(e)}")
            return False

    def mark_faq_insufficient(self, question_id: int) -> bool:
        """Mark FAQ response as insufficient"""
        try:
            with sqlite3.connect(QUESTION_DB_PATH) as conn:
                conn.execute('''
                    UPDATE questions
                    SET faq_status = 'insufficient',
                        faq_response_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (question_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error marking FAQ as insufficient: {str(e)}")
            return False

    def check_and_auto_resolve_faqs(self) -> List[Dict]:
        """Check and auto-resolve FAQ questions that have been pending for too long"""
        try:
            with sqlite3.connect(QUESTION_DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                # Get questions that have FAQ responses but no user response for over 12 hours
                cursor = conn.execute('''
                    SELECT id, channel_id, message_id, thread_id
                    FROM questions
                    WHERE resolved_at IS NULL
                    AND faq_status IS NULL
                    AND faq_response_at IS NOT NULL
                    AND datetime(faq_response_at, '+12 hours') <= datetime('now')
                ''')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error checking auto-resolve FAQs: {str(e)}")
            return []

    def record_faq_response(self, question_id: int) -> bool:
        """Record that a FAQ response was provided"""
        try:
            with sqlite3.connect(QUESTION_DB_PATH) as conn:
                conn.execute('''
                    UPDATE questions
                    SET faq_response_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (question_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error recording FAQ response: {str(e)}")
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
                           resolved_at IS NOT NULL as is_resolved,
                           faq_response_at IS NOT NULL as has_faq,
                           resolved_at IS NULL AND faq_response_at IS NOT NULL as has_pending_faq
                    FROM questions
                    ORDER BY created_at DESC
                ''')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting all question states: {str(e)}")
            return [] 