# import cv2
# import os
# import time
# import numpy as np
# from datetime import datetime
# from zoneinfo import ZoneInfo
# from ultralytics import YOLO
# from config.config import settings
# from config.enhanced_logger import EnhancedLogger
# from database.db import DatabaseManager

# class ProfileProcessor:
#     def __init__(self):
#         self.model = YOLO(settings.MODEL_PATH)
#         self.line_counter = self.LineCounter()
#         self.start_time = datetime.now(ZoneInfo("Asia/Tehran"))
#         self.duration_hours = settings.REPORT_DURATION_HOURS
#         self.stop_requested = False
#         self.db = DatabaseManager()
#         self.elog = EnhancedLogger("ProfileProcessor")
#         self.frame_count = 0

#     class LineCounter:
#         def __init__(self):
#             self.counted_ids = set()
#             self.track_history = {}
#             self.count = 0

#         def update(self, track_id, center_x, center_y, line_y):
#             if track_id not in self.track_history:
#                 self.track_history[track_id] = []
            
#             self.track_history[track_id].append(center_y)
#             if len(self.track_history[track_id]) > 2:
#                 self.track_history[track_id].pop(0)

#             if len(self.track_history[track_id]) == 2:
#                 prev_y = self.track_history[track_id][0]
#                 curr_y = self.track_history[track_id][1]

#                 if track_id not in self.counted_ids:
#                     # عبور از پایین به بالا (Y کم می‌شود)
#                     if prev_y > line_y and curr_y <= line_y:
#                         self.count += 1
#                         self.counted_ids.add(track_id)
#                         return True
#             return False

#     def process_frame(self, frame, stream_id, latency, frame_count):
#         """پردازش فریم و شمارش پروفیل‌ها"""
#         # بررسی مدت زمان گزارش‌گیری
#         if self.duration_hours is not None:
#             elapsed = (datetime.now(ZoneInfo("Asia/Tehran")) - self.start_time).total_seconds() / 3600
#             if elapsed >= self.duration_hours:
#                 self.stop_requested = True
#                 self.elog.info(f"⏰ REPORT_DURATION_HOURS ({self.duration_hours}h) exceeded. Stopping processing.")
#                 return

#         # تنظیمات ROI از config
#         lx = settings.LINE_LEFT_X
#         rx = settings.LINE_RIGHT_X
#         ly = settings.LINE_HORIZONTAL

#         # اندازه‌گیری زمان پردازش
#         start_inference = time.time()
#         results = self.model.track(frame, persist=True, verbose=False, conf=0.3)
#         inference_time = time.time() - start_inference

#         # پردازش فریم
#         annotated_frame = frame.copy()
#         cv2.line(annotated_frame, (rx, 0), (rx, frame.shape[0]), (0, 0, 255), 3)  # خط راست
#         cv2.line(annotated_frame, (lx, 0), (lx, frame.shape[0]), (0, 255, 0), 3)  # خط چپ
#         cv2.line(annotated_frame, (lx, ly), (rx, ly), (255, 255, 255), 4)        # خط افقی

#         if results and results[0].boxes and results[0].boxes.id is not None:
#             boxes = results[0].boxes.xyxy.cpu().numpy()
#             track_ids = results[0].boxes.id.int().cpu().numpy()
            
#             for box, track_id in zip(boxes, track_ids):
#                 x1, y1, x2, y2 = map(int, box)
#                 cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                
#                 in_horizontal_range = lx < cx < rx
#                 if in_horizontal_range:
#                     # رسم نقطه مرکزی (زرد، BOLD)
#                     cv2.circle(annotated_frame, (cx, cy), 5, (0, 255, 255), 3)  # زرد، ضخامت 3
                    
#                     crossed = self.line_counter.update(track_id, cx, cy, ly)
#                     if crossed:
#                         # رسم باکس (بنفش، BOLD)
#                         color = (255, 0, 255)  # بنفش
#                         label = f"ID:{track_id} Counted"
#                         cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 3)  # ضخامت 3
#                         cv2.putText(annotated_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 3)
                        
#                         # لاگ شمارش
#                         self.elog.log_line_crossing(frame_count, self.line_counter.count, track_id)
                        
#                         # ذخیره فریم پردازش شده
#                         output_path = f"/app/outputs/frame_{frame_count}.jpg"
#                         cv2.imwrite(output_path, annotated_frame)
                        
#                         # ثبت در دیتابیس
#                         self.db.insert_record()
                        
#                         # نمایش تعداد کل روی فریم
#                         cv2.putText(annotated_frame, f"Total Count: {self.line_counter.count}", 
#                                    (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)

#                     else:
#                         # رسم باکس (قرمز، BOLD)
#                         color = (0, 0, 255)  # قرمز
#                         label = f"ID:{track_id}"
#                         cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 3)  # ضخامت 3
#                         cv2.putText(annotated_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 3)

#         # لاگ خلاصه فریم
#         self.elog.log_frame_summary(
#             stream_id,
#             "CUDA:0",
#             latency,
#             inference_time,
#             42  # مصرف VRAM (مقدار نمونه)
#         )

#     def should_stop(self):
#         """بررسی اینکه آیا باید پردازش متوقف شود"""
#         return self.stop_requested


import cv2
import os
import time
import numpy as np
from datetime import datetime
from zoneinfo import ZoneInfo
from ultralytics import YOLO
from config.config import settings
from config.enhanced_logger import EnhancedLogger
from database.db import DatabaseManager
class ProfileProcessor:
    def __init__(self):
        self.model = YOLO(settings.MODEL_PATH)
        self.line_counter = self.LineCounter()
        self.start_time = datetime.now(ZoneInfo("Asia/Tehran"))
        self.duration_hours = settings.REPORT_DURATION_HOURS
        self.stop_requested = False
        self.db = DatabaseManager()
        self.elog = EnhancedLogger("ProfileProcessor")
        self.frame_count = 0
    class LineCounter:
        def __init__(self):
            self.counted_ids = set()
            self.track_history = {}
            self.count = 0
        def update(self, track_id, center_x, center_y, line_y):
            if track_id not in self.track_history:
                self.track_history[track_id] = []
            
            self.track_history[track_id].append(center_y)
            if len(self.track_history[track_id]) > 2:
                self.track_history[track_id].pop(0)
            if len(self.track_history[track_id]) == 2:
                prev_y = self.track_history[track_id][0]
                curr_y = self.track_history[track_id][1]
                if track_id not in self.counted_ids:
                    # عبور از پایین به بالا (Y کم می‌شود)
                    if prev_y > line_y and curr_y <= line_y:
                        self.count += 1
                        self.counted_ids.add(track_id)
                        return True
            return False
    def process_frame(self, frame, stream_id, latency, frame_count):
        """پردازش فریم و شمارش پروفیل‌ها"""
        # بررسی مدت زمان گزارش‌گیری
        if self.duration_hours is not None:
            elapsed = (datetime.now(ZoneInfo("Asia/Tehran")) - self.start_time).total_seconds() / 3600
            if elapsed >= self.duration_hours:
                self.stop_requested = True
                self.elog.info(f"⏰ REPORT_DURATION_HOURS ({self.duration_hours}h) exceeded. Stopping processing.")
                return
        # تنظیمات ROI از config
        lx = settings.LINE_LEFT_X
        rx = settings.LINE_RIGHT_X
        ly = settings.LINE_HORIZONTAL
        # اندازه‌گیری زمان پردازش
        start_inference = time.time()
        results = self.model.track(frame, persist=True, verbose=False, conf=0.3)
        inference_time = time.time() - start_inference
        # پردازش فریم
        annotated_frame = frame.copy()
        cv2.line(annotated_frame, (rx, 0), (rx, frame.shape[0]), (0, 0, 255), 3)  # خط راست
        cv2.line(annotated_frame, (lx, 0), (lx, frame.shape[0]), (0, 255, 0), 3)  # خط چپ
        cv2.line(annotated_frame, (lx, ly), (rx, ly), (255, 255, 255), 4)        # خط افقی
        if results and results[0].boxes and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.int().cpu().numpy()
            
            for box, track_id in zip(boxes, track_ids):
                x1, y1, x2, y2 = map(int, box)
                cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                
                in_horizontal_range = lx < cx < rx
                if in_horizontal_range:
                    # رسم نقطه مرکزی (زرد، BOLD)
                    cv2.circle(annotated_frame, (cx, cy), 5, (0, 255, 255), 3)  # زرد، ضخامت 3
                    
                    crossed = self.line_counter.update(track_id, cx, cy, ly)
                    if crossed:
                        # رسم باکس (بنفش، BOLD)
                        color = (255, 0, 255)  # بنفش
                        label = f"ID:{track_id} Counted"
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 3)  # ضخامت 3
                        cv2.putText(annotated_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 3)
                        
                        # لاگ شمارش
                        self.elog.log_line_crossing(frame_count, self.line_counter.count, track_id)
                        
                        # # ذخیره فریم پردازش شده
                        # output_path = f"/app/outputs/frame_{frame_count}.jpg"
                        
                        # # ✅ افزودن نمایش Total Count با پس‌زمینه مشکی و متن سفید
                        # text = f"Total Count: {self.line_counter.count}"
                        # font = cv2.FONT_HERSHEY_SIMPLEX
                        # font_scale = 1.5
                        # thickness = 3
                        # (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
                        # # رسم پس‌زمینه مشکی
                        # cv2.rectangle(annotated_frame, (0, 0), (text_width + 10, text_height + 10), (0, 0, 0), -1)
                        # # رسم متن سفید
                        # cv2.putText(annotated_frame, text, (5, text_height + 5), font, font_scale, (255, 255, 255), thickness)
                        
                        # # cv2.imwrite(output_path, annotated_frame)

                        # ثبت در دیتابیس
                        self.db.insert_record()
        # لاگ خلاصه فریم
        self.elog.log_frame_summary(
            stream_id,
            "CUDA:0",
            latency,
            inference_time,
            # 42  # مصرف VRAM (مقدار نمونه)
        )
    def should_stop(self):
        """بررسی اینکه آیا باید پردازش متوقف شود"""
        return self.stop_requested