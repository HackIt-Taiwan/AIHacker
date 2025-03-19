import sqlite3
import os
import logging
from typing import Optional, Dict, List, Tuple
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ModerationDB:
    """Database manager for tracking moderation actions and user violations."""
    
    def __init__(self, db_path: str = "data/moderation.db"):
        """
        Initialize the moderation database.
        
        Args:
            db_path: Path to the SQLite database file
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.conn = None
        self.create_tables()
    
    def get_connection(self):
        """Get a connection to the database."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def create_tables(self):
        """Create necessary tables if they don't exist."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create violations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            content TEXT,
            violation_categories TEXT,
            details TEXT,
            muted BOOLEAN DEFAULT FALSE
        )
        ''')
        
        # Create mutes table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS mutes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            violation_count INTEGER NOT NULL,
            active BOOLEAN DEFAULT TRUE
        )
        ''')
        
        conn.commit()
    
    def add_violation(self, user_id: int, guild_id: int, content: Optional[str] = None, 
                      violation_categories: Optional[List[str]] = None, 
                      details: Optional[Dict] = None) -> int:
        """
        Record a content violation.
        
        Args:
            user_id: Discord user ID
            guild_id: Discord guild ID
            content: The flagged content (optional)
            violation_categories: List of violation categories
            details: Additional details about the violation
            
        Returns:
            The ID of the newly created violation record
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        timestamp = datetime.utcnow().isoformat()
        
        # Convert lists and dicts to JSON strings for storage
        if violation_categories:
            violation_categories_json = json.dumps(violation_categories)
        else:
            violation_categories_json = None
            
        if details:
            details_json = json.dumps(details)
        else:
            details_json = None
        
        cursor.execute('''
        INSERT INTO violations 
        (user_id, guild_id, timestamp, content, violation_categories, details, muted)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, guild_id, timestamp, content, violation_categories_json, details_json, False))
        
        conn.commit()
        
        return cursor.lastrowid
    
    def get_violation_count(self, user_id: int, guild_id: int) -> int:
        """
        Get the number of violations for a user in a guild.
        
        Args:
            user_id: Discord user ID
            guild_id: Discord guild ID
            
        Returns:
            Number of violations
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT COUNT(*) FROM violations 
        WHERE user_id = ? AND guild_id = ?
        ''', (user_id, guild_id))
        
        result = cursor.fetchone()
        return result[0] if result else 0
    
    def add_mute(self, user_id: int, guild_id: int, violation_count: int, 
                duration: Optional[timedelta] = None) -> int:
        """
        Record a mute action.
        
        Args:
            user_id: Discord user ID
            guild_id: Discord guild ID
            violation_count: The count of violations that triggered this mute
            duration: Duration of the mute (None for permanent)
            
        Returns:
            The ID of the newly created mute record
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        start_time = datetime.utcnow()
        
        if duration:
            end_time = (start_time + duration).isoformat()
        else:
            end_time = None
        
        cursor.execute('''
        INSERT INTO mutes 
        (user_id, guild_id, start_time, end_time, violation_count, active)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, guild_id, start_time.isoformat(), end_time, violation_count, True))
        
        # Mark the latest violation as muted
        # First get the ID of the latest violation
        cursor.execute('''
        SELECT id FROM violations
        WHERE user_id = ? AND guild_id = ?
        ORDER BY id DESC LIMIT 1
        ''', (user_id, guild_id))
        
        latest_violation = cursor.fetchone()
        if latest_violation:
            # Then update that specific violation
            cursor.execute('''
            UPDATE violations
            SET muted = TRUE
            WHERE id = ?
            ''', (latest_violation[0],))
        
        conn.commit()
        
        return cursor.lastrowid
    
    def get_active_mute(self, user_id: int, guild_id: int) -> Optional[Dict]:
        """
        Get active mute for a user if it exists.
        
        Args:
            user_id: Discord user ID
            guild_id: Discord guild ID
            
        Returns:
            Dictionary with mute information or None if no active mute
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM mutes 
        WHERE user_id = ? AND guild_id = ? AND active = TRUE
        ORDER BY id DESC LIMIT 1
        ''', (user_id, guild_id))
        
        result = cursor.fetchone()
        
        if not result:
            return None
        
        mute_info = dict(result)
        
        # Convert end_time string to datetime if it exists
        if mute_info['end_time']:
            end_time = datetime.fromisoformat(mute_info['end_time'])
            now = datetime.utcnow()
            
            # If mute has expired, deactivate it
            if now > end_time:
                self._deactivate_mute(mute_info['id'])
                return None
        
        return mute_info
    
    def _deactivate_mute(self, mute_id: int) -> bool:
        """
        Deactivate a mute (internal method).
        
        Args:
            mute_id: ID of the mute to deactivate
            
        Returns:
            True if successful, False otherwise
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE mutes
            SET active = FALSE
            WHERE id = ?
            ''', (mute_id,))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error deactivating mute: {str(e)}")
            return False
    
    def check_and_update_expired_mutes(self) -> List[Dict]:
        """
        Check for expired mutes and deactivate them.
        
        Returns:
            List of deactivated mutes with user and guild IDs
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        # Find expired but still active mutes
        cursor.execute('''
        SELECT id, user_id, guild_id, violation_count
        FROM mutes 
        WHERE active = TRUE AND end_time IS NOT NULL AND end_time < ?
        ''', (now,))
        
        expired_mutes = [dict(row) for row in cursor.fetchall()]
        
        # Deactivate expired mutes
        if expired_mutes:
            mute_ids = [mute['id'] for mute in expired_mutes]
            placeholders = ','.join(['?'] * len(mute_ids))
            
            cursor.execute(f'''
            UPDATE mutes
            SET active = FALSE
            WHERE id IN ({placeholders})
            ''', mute_ids)
            
            conn.commit()
        
        return expired_mutes
    
    def calculate_mute_duration(self, violation_count: int) -> Optional[timedelta]:
        """
        Calculate mute duration based on violation count.
        
        Args:
            violation_count: Number of violations
            
        Returns:
            A timedelta for the mute duration
        """
        if violation_count == 1:
            return timedelta(minutes=5)
        elif violation_count == 2:
            return timedelta(hours=12)
        elif violation_count == 3:
            return timedelta(days=7)
        elif violation_count == 4:
            return timedelta(days=7)
        else:  # 5+ violations
            return timedelta(days=28)  # 28 days (maximum Discord timeout)
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None 