import sqlite3
import os
from datetime import datetime
from .config import WELCOMED_MEMBERS_DB_PATH
from typing import List, Dict

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
                    welcome_status TEXT DEFAULT 'pending',  -- pending, success, failed
                    retry_count INTEGER DEFAULT 0,
                    last_retry_at DATETIME,
                    UNIQUE(user_id, guild_id)
                )
            ''')
            
            # 檢查是否需要添加新欄位
            cursor = conn.execute("PRAGMA table_info(welcomed_members)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'welcome_status' not in columns:
                conn.execute('ALTER TABLE welcomed_members ADD COLUMN welcome_status TEXT DEFAULT "pending"')
            if 'retry_count' not in columns:
                conn.execute('ALTER TABLE welcomed_members ADD COLUMN retry_count INTEGER DEFAULT 0')
            if 'last_retry_at' not in columns:
                conn.execute('ALTER TABLE welcomed_members ADD COLUMN last_retry_at DATETIME')
            
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
                        username = ?,
                        retry_count = CASE WHEN welcome_status = 'success' THEN 0 ELSE retry_count END,
                        last_retry_at = CASE WHEN welcome_status = 'success' THEN NULL ELSE last_retry_at END
                    WHERE user_id = ? AND guild_id = ?
                    RETURNING join_count, welcome_status
                ''', (username, user_id, guild_id))
                
                result = cursor.fetchone()
                
                if result:
                    # 記錄已存在，返回更新後的加入次數和歡迎狀態
                    join_count, welcome_status = result
                    return welcome_status != 'success', join_count
                
                # 如果記錄不存在，創建新記錄
                conn.execute('''
                    INSERT INTO welcomed_members 
                    (user_id, guild_id, username, welcome_status)
                    VALUES (?, ?, ?, 'pending')
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
                    SELECT username, join_count, first_welcomed_at, last_welcomed_at, welcome_status
                    FROM welcomed_members
                    WHERE user_id = ? AND guild_id = ?
                ''', (user_id, guild_id))
                result = cursor.fetchone()
                
                if result:
                    return {
                        'username': result[0],
                        'join_count': result[1],
                        'first_welcomed_at': result[2],
                        'last_welcomed_at': result[3],
                        'welcome_status': result[4]
                    }
                return None
        except Exception as e:
            print(f"Error getting member info: {str(e)}")
            return None

    def mark_welcome_success(self, user_id: int, guild_id: int):
        """標記歡迎訊息發送成功"""
        try:
            with sqlite3.connect(WELCOMED_MEMBERS_DB_PATH) as conn:
                conn.execute('''
                    UPDATE welcomed_members
                    SET welcome_status = 'success',
                        last_welcomed_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND guild_id = ?
                ''', (user_id, guild_id))
                conn.commit()
        except Exception as e:
            print(f"Error marking welcome success: {str(e)}")

    def mark_welcome_failed(self, user_id: int, guild_id: int):
        """標記歡迎訊息發送失敗"""
        try:
            with sqlite3.connect(WELCOMED_MEMBERS_DB_PATH) as conn:
                conn.execute('''
                    UPDATE welcomed_members
                    SET welcome_status = 'failed',
                        retry_count = retry_count + 1,
                        last_retry_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND guild_id = ?
                ''', (user_id, guild_id))
                conn.commit()
        except Exception as e:
            print(f"Error marking welcome failed: {str(e)}")

    def get_pending_welcomes(self, max_retry: int = 3, retry_interval_minutes: int = 5) -> List[Dict]:
        """獲取需要重試的歡迎記錄"""
        try:
            with sqlite3.connect(WELCOMED_MEMBERS_DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT user_id, guild_id, username, retry_count, last_retry_at
                    FROM welcomed_members
                    WHERE (welcome_status = 'pending' OR welcome_status = 'failed')
                    AND retry_count < ?
                    AND (last_retry_at IS NULL OR 
                         datetime(last_retry_at, '+' || ? || ' minutes') <= datetime('now'))
                    ORDER BY last_retry_at ASC
                ''', (max_retry, retry_interval_minutes))
                
                return [{
                    'user_id': row['user_id'],
                    'guild_id': row['guild_id'],
                    'username': row['username'],
                    'retry_count': row['retry_count']
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting pending welcomes: {str(e)}")
            return [] 