# src/api/reports.py
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from database.db import DatabaseManager
import threading
import time

logger = logging.getLogger(__name__)

class StatsReporter:
    def __init__(self):
        self.running = True

    def run_periodic_reporting(self):
        """گزارش‌گیری ساعتی — فقط لاگ می‌شود، هیچ فایلی نوشته نمی‌شود"""
        while self.running:
            time.sleep(55)          # برای تست سریع — در تولید معمولاً 3600 ثانیه
            self.report_hourly()

    def report_hourly(self):
        """گزارش تعداد اشیاء در آخرین ساعت — فقط به لاگر"""
        db = DatabaseManager()
        now = datetime.now(ZoneInfo("Asia/Tehran"))
        start_time = (now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        end_time = now.strftime('%Y-%m-%d %H:%M:%S')
        
        data = db.get_counts(start_time=start_time, end_time=end_time)
        count = len(data)
        
        logger.info(f"📊 Hourly Report: {now.strftime('%Y-%m-%d %H:00')} | Count: {count}")