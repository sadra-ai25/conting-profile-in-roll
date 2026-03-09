import sqlite3
import os
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

# تنظیم logging
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path="/app/outputs/production.db"):
        """
        ایجاد ارتباط با دیتابیس SQLite.
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.create_table()
        logger.info(f"💾 SQLite Database connected at: {self.db_path}")

    def create_table(self):
        """ایجاد جدول اگر وجود نداشته باشد طبق ساختار جدید"""
        query = """
        CREATE TABLE IF NOT EXISTS profile_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            count INTEGER NOT NULL,
            timestamp DATETIME NOT NULL
        )
        """
        try:
            self.conn.execute(query)
            self.conn.commit()
        except Exception as e:
            logger.error(f"❌ Failed to create SQLite table: {e}")

    def insert_record(self):
        """
        درج رکورد جدید شامل عدد ۱ برای فیلد count و زمان فعلی تهران.
        """
        try:
            tehran_tz = ZoneInfo("Asia/Tehran")
            current_time = datetime.now(tehran_tz).strftime('%Y-%m-%d %H:%M:%S')
            # درج عدد 1 در ستون count طبق خواسته شما
            query = "INSERT INTO profile_logs (count, timestamp) VALUES (?, ?)"
            self.conn.execute(query, (1, current_time))
            self.conn.commit()
        except Exception as e:
            logger.error(f"❌ Database Insert Error: {e}")

    def get_counts(self, start_time=None, end_time=None):
        """
        خواندن رکوردها شامل count و timestamp
        """
        try:
            cursor = self.conn.cursor()
            query = "SELECT id, count, timestamp FROM profile_logs"
            params = []
            
            conditions = []
            if start_time:
                conditions.append("timestamp >= ?")
                params.append(start_time)
            if end_time:
                conditions.append("timestamp <= ?")
                params.append(end_time)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            data = [dict(zip(columns, row)) for row in rows]
                
            return data
        except Exception as e:
            logger.error(f"❌ Failed to read from database: {e}")
            return []

    def close(self):
        self.conn.close()