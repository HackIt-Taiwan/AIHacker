import os
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict

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
                    UNIQUE(user_id, guild_id, start_date, end_date)
                )
            ''')
            conn.commit()

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