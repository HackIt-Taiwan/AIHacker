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
import logging
from app.config import (
    QUESTION_DB_PATH, QUESTION_RESOLVER_ROLES,
    QUESTION_EMOJI, QUESTION_RESOLVED_EMOJI,
    QUESTION_FAQ_FOUND_EMOJI, QUESTION_FAQ_PENDING_EMOJI
)

# 設置日誌
logger = logging.getLogger('question_manager')
logger.setLevel(logging.INFO)

# 確保日誌目錄存在
os.makedirs('logs', exist_ok=True)

# 設置檔案處理器
file_handler = logging.FileHandler('logs/question_manager.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)

# 設置日誌格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# 添加處理器到日誌記錄器
logger.addHandler(file_handler)

class FAQResponseButton(Button):
    # 用於追踪正在處理中的按鈕
    _processing_buttons = set()

    def __init__(self, question_id: int, is_resolved: bool, response_type: str):
        # Initialize button with appropriate style based on response type
        super().__init__(
            style=discord.ButtonStyle.green if response_type == "resolved" else discord.ButtonStyle.secondary,
            label="✨ 已解決問題" if response_type == "resolved" else "💭 需要更多協助",
            custom_id=f"faq_response_{question_id}_{response_type}",
            disabled=is_resolved
        )
        self.question_id = question_id
        self.response_type = response_type

    async def callback(self, interaction: discord.Interaction):
        # 檢查按鈕是否正在處理中
        button_id = f"{self.question_id}_{self.response_type}"
        if button_id in self._processing_buttons:
            logger.info(f"FAQ按鈕正在處理中 - 問題ID: {self.question_id}, 用戶: {interaction.user.name}({interaction.user.id})")
            await interaction.response.send_message("💫 正在處理您的回應...", ephemeral=True)
            return

        # 將按鈕標記為處理中
        self._processing_buttons.add(button_id)
        logger.info(f"開始處理FAQ回應 - 問題ID: {self.question_id}, 用戶: {interaction.user.name}({interaction.user.id}), 回應類型: {self.response_type}")

        try:
            question_manager = QuestionManager()
            question = question_manager.get_question(self.question_id)
            
            if not question:
                logger.error(f"找不到問題記錄 - 問題ID: {self.question_id}")
                await interaction.response.send_message("❌ 無法找到此問題的記錄", ephemeral=True)
                return
                
            if interaction.user.id != question['user_id']:
                logger.warning(f"非提問者嘗試回應FAQ - 問題ID: {self.question_id}, 用戶: {interaction.user.name}({interaction.user.id})")
                await interaction.response.send_message("💡 只有提問者可以回應 FAQ 的幫助程度", ephemeral=True)
                return

            # 立即回應交互以避免超時
            await interaction.response.defer(ephemeral=True)

            try:
                # 先禁用所有按鈕以防止重複點擊
                view = self.view
                for item in view.children:
                    item.disabled = True
                await interaction.message.edit(view=view)
                logger.info(f"已禁用FAQ按鈕 - 問題ID: {self.question_id}")

                if self.response_type == "resolved":
                    # Mark question as resolved by FAQ
                    if question_manager.mark_question_resolved(self.question_id, None, resolution_type="faq"):
                        logger.info(f"問題已被FAQ解決 - 問題ID: {self.question_id}, 用戶: {interaction.user.name}({interaction.user.id})")
                        # Update original message reactions
                        try:
                            channel = interaction.guild.get_channel(question['channel_id'])
                            if channel:
                                message = await channel.fetch_message(question['message_id'])
                                if message:
                                    await message.clear_reactions()
                                    await message.add_reaction(QUESTION_RESOLVED_EMOJI)
                                    
                                    # 找到並禁用所有相關按鈕
                                    async for msg in interaction.channel.history(limit=50):
                                        if msg.author == interaction.client.user:
                                            # 檢查是否為原始問題按鈕
                                            if "已收到您的問題！" in msg.content:
                                                view = discord.ui.View.from_message(msg)
                                                for item in view.children:
                                                    item.disabled = True
                                                await msg.edit(view=view)
                                            # 檢查是否為 FAQ 回應按鈕
                                            elif "找到相關的 FAQ" in msg.content:
                                                view = discord.ui.View.from_message(msg)
                                                for item in view.children:
                                                    item.disabled = True
                                                await msg.edit(view=view)
                        except Exception as e:
                            print(f"Error updating reactions or buttons: {str(e)}")
                        
                        await interaction.followup.send("✨ 感謝您的回饋！\n很高興 FAQ 能夠解決您的問題", ephemeral=True)
                        await interaction.channel.send("🎉 **問題已解決**\n此問題已透過 FAQ 成功解答")
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
                    
                    await interaction.followup.send("💫 感謝您的回饋！\n我們會盡快為您提供進一步協助", ephemeral=True)
                    await interaction.channel.send("💭 **需要更多協助**\n提問者表示需要進一步的說明，請相關人員協助回答")
            except Exception as e:
                print(f"Error handling FAQ response: {str(e)}")
                try:
                    await interaction.followup.send("⚠️ 處理回應時發生問題，請稍後再試", ephemeral=True)
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
            style=discord.ButtonStyle.green if not is_resolved else discord.ButtonStyle.secondary,
            label="標記已解決" if not is_resolved else "已標記完成",
            custom_id=f"resolve_question_{question_id}",
            disabled=is_resolved
        )
        self.question_id = question_id

    async def callback(self, interaction: discord.Interaction):
        # 檢查是否有解決問題的權限
        if not any(role.id in QUESTION_RESOLVER_ROLES for role in interaction.user.roles):
            logger.warning(f"用戶嘗試無權限操作 - 用戶: {interaction.user.name}({interaction.user.id}), 問題ID: {self.question_id}")
            await interaction.response.send_message(
                "💡 此操作需要特定的權限\n"
                "如果您需要標記問題解決，請聯繫工作人員協助",
                ephemeral=True
            )
            return

        # 立即回應互動以避免超時
        await interaction.response.defer(ephemeral=True)
        logger.info(f"開始處理問題解決標記 - 問題ID: {self.question_id}, 工作人員: {interaction.user.name}({interaction.user.id})")

        question_manager = QuestionManager()
        
        # Mark question as resolved
        if question_manager.mark_question_resolved(self.question_id, interaction.user.id):
            # Update button state
            self.style = discord.ButtonStyle.secondary
            self.label = "已標記完成"
            self.disabled = True
            
            # Update view
            view = self.view
            for item in view.children:
                item.disabled = True
            await interaction.message.edit(view=view)
            
            # Update original message reaction and disable all related buttons
            try:
                question = question_manager.get_question(self.question_id)
                if question:
                    channel = interaction.guild.get_channel(question['channel_id'])
                    if channel:
                        # Update original message reaction
                        message = await channel.fetch_message(question['message_id'])
                        if message:
                            await message.clear_reactions()
                            await message.add_reaction(QUESTION_RESOLVED_EMOJI)
                        
                        # Find and disable all related buttons in the thread
                        async for msg in interaction.channel.history(limit=50):
                            if msg.author == interaction.client.user:
                                try:
                                    # 檢查是否為 FAQ 回應按鈕
                                    if "智能解答" in msg.embeds[0].title:
                                        view = discord.ui.View.from_message(msg)
                                        for item in view.children:
                                            item.disabled = True
                                        await msg.edit(view=view)
                                except (IndexError, AttributeError):
                                    pass  # 跳過沒有 embed 或其他格式的訊息
            except Exception as e:
                print(f"Error updating message reaction or buttons: {str(e)}")
            
            await interaction.followup.send("✨ 已將問題標記為已解決", ephemeral=True)
            await interaction.channel.send(f"✨ 此問題已由 {interaction.user.mention} 標記為已解決")

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
                question_id = cursor.lastrowid
                logger.info(f"新問題已添加 - ID: {question_id}, 用戶ID: {user_id}, 頻道: {channel_id}")
                return question_id
        except sqlite3.IntegrityError:
            logger.error(f"添加問題失敗(重複記錄) - 頻道: {channel_id}, 訊息: {message_id}")
            return None
        except Exception as e:
            logger.error(f"添加問題記錄時發生錯誤: {str(e)}")
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
                logger.info(f"問題已標記為已解決 - ID: {question_id}, 解決者: {resolver_id}, 類型: {resolution_type}")
                return True
        except Exception as e:
            logger.error(f"標記問題已解決時發生錯誤 - ID: {question_id}, 錯誤: {str(e)}")
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
                logger.info(f"FAQ回應被標記為不足 - 問題ID: {question_id}")
                return True
        except Exception as e:
            logger.error(f"標記FAQ不足時發生錯誤 - 問題ID: {question_id}, 錯誤: {str(e)}")
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
                logger.info(f"已記錄FAQ回應 - 問題ID: {question_id}")
                return True
        except Exception as e:
            logger.error(f"記錄FAQ回應時發生錯誤 - 問題ID: {question_id}, 錯誤: {str(e)}")
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
                           resolved_at IS NULL AND faq_response_at IS NOT NULL as has_pending_faq,
                           faq_response_at,
                           datetime(faq_response_at, '+12 hours') <= datetime('now') as is_faq_expired
                    FROM questions
                    ORDER BY created_at DESC
                ''')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting all question states: {str(e)}")
            return [] 