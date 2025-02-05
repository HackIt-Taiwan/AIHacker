import os
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Literal

class LeaveManager:
    def __init__(self, db_path: str = "data/leaves.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._ensure_db()

    def _ensure_db(self):
        """確保資料庫存在並有正確的結構"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS leaves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    reason TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    announcement_msg_id INTEGER,
                    announcement_channel_id INTEGER,
                    UNIQUE(user_id, guild_id, start_date, end_date)
                )
            ''')
            conn.commit()

    def get_leave_status(self, start_date: datetime, end_date: datetime, current_time: datetime = None) -> Literal['pending', 'active', 'expired']:
        """
        獲取請假狀態
        - pending: 尚未開始
        - active: 正在進行中
        - expired: 已結束
        """
        if current_time is None:
            current_time = datetime.now()

        current_date = current_time.date()
        start_date = start_date.date()
        end_date = end_date.date()

        if current_date < start_date:
            return 'pending'
        elif current_date > end_date:
            return 'expired'
        else:
            return 'active'

    def add_leave(self, user_id: int, guild_id: int, start_date: datetime, end_date: datetime, reason: str = None) -> bool:
        """添加請假記錄"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO leaves (user_id, guild_id, start_date, end_date, reason)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, guild_id, start_date.strftime('%Y-%m-%d'), 
                     end_date.strftime('%Y-%m-%d'), reason))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"添加請假記錄時發生錯誤: {str(e)}")
            return False

    def update_announcement_message(self, leave_id: int, msg_id: int, channel_id: int) -> bool:
        """更新請假公告訊息的ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE leaves 
                    SET announcement_msg_id = ?, announcement_channel_id = ?
                    WHERE id = ?
                ''', (msg_id, channel_id, leave_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"更新請假公告訊息ID時發生錯誤: {str(e)}")
            return False

    def get_announcement_info(self, leave_id: int) -> Optional[Dict]:
        """獲取請假公告訊息的資訊"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT announcement_msg_id, announcement_channel_id
                    FROM leaves
                    WHERE id = ?
                ''', (leave_id,))
                row = cursor.fetchone()
                if row:
                    return {
                        'msg_id': row['announcement_msg_id'],
                        'channel_id': row['announcement_channel_id']
                    }
                return None
        except Exception as e:
            print(f"獲取請假公告訊息資訊時發生錯誤: {str(e)}")
            return None

    def get_all_active_leaves(self) -> List[Dict]:
        """獲取所有進行中或待開始的請假記錄"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT id, user_id, guild_id, start_date, end_date, reason,
                           announcement_msg_id, announcement_channel_id
                    FROM leaves
                    WHERE date(end_date) >= date('now')
                    ORDER BY start_date ASC
                ''')
                
                leaves = []
                for row in cursor:
                    leaves.append({
                        'id': row['id'],
                        'user_id': row['user_id'],
                        'guild_id': row['guild_id'],
                        'start_date': datetime.strptime(row['start_date'], '%Y-%m-%d'),
                        'end_date': datetime.strptime(row['end_date'], '%Y-%m-%d'),
                        'reason': row['reason'],
                        'announcement_msg_id': row['announcement_msg_id'],
                        'announcement_channel_id': row['announcement_channel_id']
                    })
                return leaves
        except Exception as e:
            print(f"獲取活動請假記錄時發生錯誤: {str(e)}")
            return []

    def get_active_leave(self, user_id: int, guild_id: int, date: datetime = None) -> Optional[Dict]:
        """獲取指定用戶在指定日期的請假記錄"""
        if date is None:
            date = datetime.now()

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT id, start_date, end_date, reason
                    FROM leaves
                    WHERE user_id = ? AND guild_id = ?
                    AND date(?) BETWEEN date(start_date) AND date(end_date)
                ''', (user_id, guild_id, date.strftime('%Y-%m-%d')))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row['id'],
                        'start_date': datetime.strptime(row['start_date'], '%Y-%m-%d'),
                        'end_date': datetime.strptime(row['end_date'], '%Y-%m-%d'),
                        'reason': row['reason']
                    }
                return None
        except Exception as e:
            print(f"獲取請假記錄時發生錯誤: {str(e)}")
            return None

    def get_user_leaves(self, user_id: int, guild_id: int) -> List[Dict]:
        """獲取用戶的所有請假記錄"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT id, start_date, end_date, reason
                    FROM leaves
                    WHERE user_id = ? AND guild_id = ?
                    ORDER BY start_date DESC
                ''', (user_id, guild_id))
                
                leaves = []
                for row in cursor:
                    leaves.append({
                        'id': row['id'],
                        'start_date': datetime.strptime(row['start_date'], '%Y-%m-%d'),
                        'end_date': datetime.strptime(row['end_date'], '%Y-%m-%d'),
                        'reason': row['reason']
                    })
                return leaves
        except Exception as e:
            print(f"獲取用戶請假記錄時發生錯誤: {str(e)}")
            return []

    def delete_leave(self, leave_id: int, user_id: int, guild_id: int) -> bool:
        """刪除請假記錄"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    DELETE FROM leaves
                    WHERE id = ? AND user_id = ? AND guild_id = ?
                ''', (leave_id, user_id, guild_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"刪除請假記錄時發生錯誤: {str(e)}")
            return False 