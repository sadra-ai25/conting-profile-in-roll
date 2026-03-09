# import redis
# import time
# import cv2
# import logging
# import pickle
# import uuid
# import os
# from zoneinfo import ZoneInfo
# from datetime import datetime, timezone
# from config.config import settings

# # تنظیمات Logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# # اتصال به ردیس
# redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

# # تنظیم تایم‌زون تهران
# TEHRAN_TZ = ZoneInfo("Asia/Tehran")

# def camera_producer(stop_event):
#     os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"    logger.info("=" * 80)
#     logger.info("🚀 Starting RTSP Camera Producer (Analysis Only Mode)...")
#     rtsp_url = settings.RTSP_URL
#     if not rtsp_url:
#         logger.error("❌ RTSP URL is not defined in .env")
#         return
    
#     cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
#     cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
#     if not cap.isOpened():
#         logger.error("❌ Failed to open RTSP stream.")
#         return
    
#     logger.info(f"✅ RTSP Connected: {rtsp_url}")
#     logger.info("=" * 80)
    
#     frame_count = 0
#     stream_name = "camera_processing_tasks"
    
#     while not stop_event.is_set():
#         ret, frame = cap.read()
#         if not ret:
#             logger.warning("⚠️ Stream lost. Reconnecting...")
#             cap.release()
#             time.sleep(3)
#             cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
#             continue
        
#         frame_count += 1
#         _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
#         frame_bytes = buffer.tobytes()
#         frame_id = str(uuid.uuid4())
        
#         # ذخیره فریم در ردیس
#         redis_client.setex(f"frame:{frame_id}", 10, frame_bytes)
        
#         # افزودن frame_count به تکست مسیج
#         task_message = {
#             'frame_id': frame_id,
#             'timestamp_tehran': datetime.now(TEHRAN_TZ).isoformat(),
#             'frame_count': frame_count  # افزودن شماره فریم
#         }
        
#         try:
#             redis_client.xadd(stream_name, {'data': pickle.dumps(task_message)}, maxlen=100)
#         except Exception as e:
#             logger.error(f"❌ Redis Write Error: {e}")
        
#         if frame_count % 100 == 0:
#             logger.debug(f"📹 Produced frame #{frame_count}")
    
#     cap.release()
#     logger.info("🛑 Camera Producer Stopped.")


import redis
import time
import cv2
import logging
import pickle
import uuid
import os
from zoneinfo import ZoneInfo
from datetime import datetime
from config.config import settings

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("capture.producer")

# ------------------------------------------------------------------------------
# Force OpenCV / FFmpeg to use TCP for RTSP  (CRITICAL)
# ------------------------------------------------------------------------------
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

# ------------------------------------------------------------------------------
# Redis
# ------------------------------------------------------------------------------
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    socket_connect_timeout=5,
    socket_timeout=5,
)

# ------------------------------------------------------------------------------
# Timezone
# ------------------------------------------------------------------------------
TEHRAN_TZ = ZoneInfo("Asia/Tehran")

# ------------------------------------------------------------------------------
# Camera Producer with Robust Reconnect
# ------------------------------------------------------------------------------
def camera_producer(stop_event):
    logger.info("=" * 80)
    logger.info("🚀 Starting RTSP Camera Producer (Rollway / Stable Mode)")
    logger.info("=" * 80)

    rtsp_url = settings.RTSP_URL
    if not rtsp_url:
        logger.error("❌ RTSP URL is not defined in .env")
        return

    stream_name = "camera_processing_tasks"
    frame_count = 0

    backoff = 3
    max_backoff = 30

    while not stop_event.is_set():

        logger.info("🔌 Connecting to RTSP...")
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            logger.warning(
                f"❌ Cannot open RTSP stream. Retrying in {backoff}s..."
            )
            time.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
            continue

        logger.info("✅ RTSP Connected")
        backoff = 3  # reset after success

        # ----------------- Frame Loop -----------------
        while not stop_event.is_set():

            ret, frame = cap.read()

            if not ret:
                logger.warning("⚠️ Stream lost. Reconnecting...")
                break

            frame_count += 1

            # Encode frame
            success, buffer = cv2.imencode(
                ".jpg",
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, 85],
            )

            if not success:
                logger.warning("⚠️ JPEG encoding failed, skipping frame")
                continue

            frame_bytes = buffer.tobytes()
            frame_id = str(uuid.uuid4())

            # Save raw frame with TTL
            try:
                redis_client.setex(
                    f"frame:{frame_id}",
                    10,
                    frame_bytes,
                )
            except Exception as e:
                logger.error(f"❌ Redis SETEX failed: {e}")

            # Push task to Redis Stream
            task_message = {
                "frame_id": frame_id,
                "timestamp_tehran": datetime.now(TEHRAN_TZ).isoformat(),
                "frame_count": frame_count,
            }

            try:
                redis_client.xadd(
                    stream_name,
                    {"data": pickle.dumps(task_message)},
                    maxlen=100,
                )
            except Exception as e:
                logger.error(f"❌ Redis XADD failed: {e}")

        # ----------------- Cleanup before reconnect -----------------
        try:
            cap.release()
        except Exception:
            pass

        logger.info("♻️ RTSP connection closed, retrying...")

        time.sleep(backoff)
        backoff = min(backoff * 2, max_backoff)

    logger.info("🛑 Camera Producer Stopped.")