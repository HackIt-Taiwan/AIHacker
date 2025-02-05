import sqlite3
import os
from datetime import datetime
from .config import WELCOMED_MEMBERS_DB_PATH

class WelcomedMembersDB:
    def __init__(self):
        # 確保資料庫目錄存在
        os.makedirs(os.path.dirname(WELCOMED_MEMBERS_DB_PATH), exist_ok=True)
        self.init_db()

    def init_db(self):
        """初始化資料庫，創建必要的表格"""
        with sqlite3.connect(WELCOMED_MEMBERS_DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS welcomed_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    join_count INTEGER DEFAULT 1,
                    first_welcomed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_welcomed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, guild_id)
                )
            ''')
            conn.commit()

    def add_or_update_member(self, user_id: int, guild_id: int, username: str) -> tuple[bool, int]:
        """
        添加或更新已歡迎的成員記錄
        返回: (是否是首次加入, 加入次數)
        """
        try:
            with sqlite3.connect(WELCOMED_MEMBERS_DB_PATH) as conn:
                # 嘗試更新現有記錄
                cursor = conn.execute('''
                    UPDATE welcomed_members 
                    SET join_count = join_count + 1,
                        last_welcomed_at = CURRENT_TIMESTAMP,
                        username = ?
                    WHERE user_id = ? AND guild_id = ?
                    RETURNING join_count
                ''', (username, user_id, guild_id))
                
                result = cursor.fetchone()
                
                if result:
                    # 記錄已存在，返回更新後的加入次數
                    return False, result[0]
                
                # 如果記錄不存在，創建新記錄
                conn.execute('''
                    INSERT INTO welcomed_members (user_id, guild_id, username)
                    VALUES (?, ?, ?)
                ''', (user_id, guild_id, username))
                conn.commit()
                return True, 1
                
        except Exception as e:
            print(f"Error adding/updating welcomed member: {str(e)}")
            return False, 0

    def get_member_join_count(self, user_id: int, guild_id: int) -> int:
        """獲取成員的加入次數"""
        try:
            with sqlite3.connect(WELCOMED_MEMBERS_DB_PATH) as conn:
                cursor = conn.execute('''
                    SELECT join_count 
                    FROM welcomed_members
                    WHERE user_id = ? AND guild_id = ?
                ''', (user_id, guild_id))
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            print(f"Error getting member join count: {str(e)}")
            return 0

    def get_member_info(self, user_id: int, guild_id: int) -> dict:
        """獲取成員的完整資訊"""
        try:
            with sqlite3.connect(WELCOMED_MEMBERS_DB_PATH) as conn:
                cursor = conn.execute('''
                    SELECT username, join_count, first_welcomed_at, last_welcomed_at
                    FROM welcomed_members
                    WHERE user_id = ? AND guild_id = ?
                ''', (user_id, guild_id))
                result = cursor.fetchone()
                
                if result:
                    return {
                        'username': result[0],
                        'join_count': result[1],
                        'first_welcomed_at': result[2],
                        'last_welcomed_at': result[3]
                    }
                return None
        except Exception as e:
            print(f"Error getting member info: {str(e)}")
            return None 