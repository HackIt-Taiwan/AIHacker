import os
import sqlite3
from datetime import datetime
import pytz
from typing import List, Dict, Optional, Tuple
from app.config import INVITE_DB_PATH, INVITE_TIME_ZONE, INVITE_LIST_PAGE_SIZE

class InviteManager:
    def __init__(self, db_path: str = INVITE_DB_PATH):
        self.db_path = db_path
        self.timezone = pytz.timezone(INVITE_TIME_ZONE)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._ensure_db()

    def _ensure_db(self):
        """確保資料庫存在並有正確的結構"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS invites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invite_code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    creator_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def add_invite(self, invite_code: str, name: str, creator_id: int, channel_id: int) -> bool:
        """添加新的邀請記錄"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO invites (invite_code, name, creator_id, channel_id)
                    VALUES (?, ?, ?, ?)
                ''', (invite_code, name, creator_id, channel_id))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"添加邀請記錄時發生錯誤: {str(e)}")
            return False

    def delete_invite(self, invite_code: str, user_id: int, guild_invites: List[Dict]) -> bool:
        """刪除邀請記錄（只能由創建者或管理員刪除）"""
        try:
            # 檢查 Discord 邀請是否存在
            invite_exists = any(inv['code'] == invite_code for inv in guild_invites)
            if not invite_exists:
                print(f"邀請連結 {invite_code} 已不存在於 Discord")
                # 如果 Discord 上已不存在，也從資料庫中刪除
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('DELETE FROM invites WHERE invite_code = ?', (invite_code,))
                    conn.commit()
                return True

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    DELETE FROM invites
                    WHERE invite_code = ? AND creator_id = ?
                ''', (invite_code, user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"刪除邀請記錄時發生錯誤: {str(e)}")
            return False

    def get_invites_page(self, page: int, guild_invites: List[Dict]) -> Tuple[List[Dict], int]:
        """獲取指定頁的邀請記錄，並結合 Discord 的使用次數"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # 獲取總記錄數
                cursor = conn.execute('SELECT COUNT(*) FROM invites')
                total_count = cursor.fetchone()[0]
                
                # 計算總頁數
                total_pages = (total_count + INVITE_LIST_PAGE_SIZE - 1) // INVITE_LIST_PAGE_SIZE
                
                # 確保頁碼有效
                page = max(1, min(page, total_pages))
                offset = (page - 1) * INVITE_LIST_PAGE_SIZE
                
                cursor = conn.execute('''
                    SELECT invite_code, name, creator_id, channel_id, created_at
                    FROM invites
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (INVITE_LIST_PAGE_SIZE, offset))
                
                invites = []
                for row in cursor:
                    # 轉換時間到指定時區
                    created_at = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
                    created_at = pytz.utc.localize(created_at).astimezone(self.timezone)
                    
                    # 從 Discord 邀請中獲取使用次數
                    uses = 0
                    for guild_invite in guild_invites:
                        if guild_invite['code'] == row['invite_code']:
                            uses = guild_invite['uses']
                            break
                    
                    invites.append({
                        'invite_code': row['invite_code'],
                        'name': row['name'],
                        'creator_id': row['creator_id'],
                        'channel_id': row['channel_id'],
                        'uses': uses,
                        'created_at': created_at
                    })
                return invites, total_pages
        except Exception as e:
            print(f"獲取邀請記錄時發生錯誤: {str(e)}")
            return [], 0 