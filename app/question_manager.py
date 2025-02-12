"""
Question manager for handling questions and their threads.
"""
import os
import sqlite3
from datetime import datetime
import discord
from discord.ui import Button, View
from typing import Optional, Dict, List
from app.config import QUESTION_DB_PATH, QUESTION_RESOLVER_ROLES

class QuestionButton(Button):
    def __init__(self, question_id: int, is_resolved: bool = False):
        super().__init__(
            style=discord.ButtonStyle.green if not is_resolved else discord.ButtonStyle.gray,
            label="已完成" if not is_resolved else "已標記完成",
            custom_id=f"resolve_question_{question_id}",
            disabled=is_resolved
        )
        self.question_id = question_id

    async def callback(self, interaction: discord.Interaction):
        # 檢查用戶是否有解答權限
        if not any(role.id in QUESTION_RESOLVER_ROLES for role in interaction.user.roles):
            await interaction.response.send_message("❌ 您沒有標記問題解決的權限！", ephemeral=True)
            return

        # 更新問題狀態
        question_manager = QuestionManager()
        
        # 獲取問題資訊以便移除表情符號
        question = question_manager.get_question(self.question_id)
        if not question:
            await interaction.response.send_message("❌ 找不到此問題！", ephemeral=True)
            return
            
        if question_manager.mark_question_resolved(self.question_id, interaction.user.id):
            # 更新按鈕狀態
            self.style = discord.ButtonStyle.gray
            self.label = "已標記完成"
            self.disabled = True
            
            # 更新原始訊息的視圖
            view = View.from_message(interaction.message)
            view.clear_items()
            view.add_item(self)
            await interaction.message.edit(view=view)
            
            # 處理原始訊息的表情符號
            try:
                channel = interaction.guild.get_channel(question['channel_id'])
                if channel:
                    message = await channel.fetch_message(question['message_id'])
                    if message:
                        await message.clear_reactions()  # 移除所有表情符號
                        await message.add_reaction('✅')  # 添加勾選表情符號
            except Exception as e:
                print(f"處理表情符號時發生錯誤: {str(e)}")
            
            # 在討論串中發送完成訊息
            await interaction.channel.send(
                f"✅ 本問題已由 {interaction.user.mention} 標記為已解決！"
            )
            
            # 不顯示確認訊息，只更新交互
            await interaction.response.defer()
        else:
            await interaction.response.send_message("❌ 標記問題解決時發生錯誤！", ephemeral=True)

class QuestionView(View):
    def __init__(self, question_id: int = 0):
        super().__init__(timeout=None)  # 永久按鈕
        
        # 如果是通用視圖（question_id = 0），不添加按鈕
        # 這個視圖只用於處理已存在的按鈕
        if question_id > 0:
            self.add_item(QuestionButton(question_id))

    @staticmethod
    def create_for_question(question_id: int, is_resolved: bool = False) -> 'QuestionView':
        """創建特定問題的視圖"""
        view = QuestionView()
        view.add_item(QuestionButton(question_id, is_resolved))
        return view

class QuestionManager:
    def __init__(self):
        os.makedirs(os.path.dirname(QUESTION_DB_PATH), exist_ok=True)
        self._ensure_db()

    def _ensure_db(self):
        """確保資料庫存在並有正確的結構"""
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
        """添加新的問題記錄，返回問題ID"""
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
            print(f"添加問題記錄時發生錯誤: {str(e)}")
            return None

    def update_thread(self, question_id: int, thread_id: int) -> bool:
        """更新問題的討論串ID"""
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
            print(f"更新問題討論串時發生錯誤: {str(e)}")
            return False

    def mark_question_resolved(self, question_id: int, resolver_id: int) -> bool:
        """將問題標記為已解決"""
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
            print(f"標記問題解決時發生錯誤: {str(e)}")
            return False

    def get_question(self, question_id: int) -> Optional[Dict]:
        """獲取問題資訊"""
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
            print(f"獲取問題資訊時發生錯誤: {str(e)}")
            return None

    def get_unresolved_questions(self) -> List[Dict]:
        """獲取所有未解決的問題"""
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
            print(f"獲取未解決問題時發生錯誤: {str(e)}")
            return [] 