import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

class EnhancedLogger:
    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)
        self.logger.propagate = False
        
        if not self.logger.handlers:
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

            self.logger.setLevel(logging.INFO)
            
        self.timezone = ZoneInfo("Asia/Tehran")

    def info(self, msg):
        self.logger.info(msg)

    def error(self, msg):
        self.logger.error(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def log_profile_event(self):
        pass

    def log_line_crossing(self, frame_id: int, total_count: int, obj_id: int):
        """لاگ برای سیستم شمارش پروفیل از روی خط افقی"""
        msg = f"🟢 Profile Crossed Horizontal Line 😂 Frame:{frame_id} | Total Count:{total_count} | Obj_ID:{obj_id}"
        self.logger.info(msg)

    def log_frame_summary(self, stream_name: str, device: str, redis_latency: float, inference_time: float, memory_usage: float = 0):
        status_icon = "⚙️"
        if inference_time > 0.100:
            status_icon = "🐢"
        lat_str = f"{redis_latency:.3f}s"
        inf_str = f"{inference_time*1000:.1f}ms"
        msg = (f"{status_icon} [{stream_name}] Processed | "
               f"Device: {device.upper()} | "
               f"Redis Latency: {lat_str} | "
               f"Inference: {inf_str}")
        self.logger.info(msg)

    def log_rtsp_stability(self, stream_name: str, status: str, details: str = ""):
        if status == "CONNECTED":
            self.logger.info(f"📹 [{stream_name}] RTSP Connected Successfully. {details}")
        elif status == "DISCONNECTED":
            self.logger.error(f"📵 [{stream_name}] RTSP Signal LOST! {details}")
        elif status == "UNSTABLE":
            self.logger.warning(f"⚠️ [{stream_name}] RTSP Unstable: {details}")