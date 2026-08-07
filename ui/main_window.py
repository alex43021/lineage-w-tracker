import os
import json
import logging
import time
import re
import cv2
import requests
import win32gui
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QTextEdit, QLabel, QGroupBox, QComboBox, QSpinBox,
                               QLineEdit, QTabWidget, QListWidget, QListWidgetItem,
                               QFileDialog, QMessageBox, QCheckBox, QStyle, QInputDialog, QTimeEdit,
                               QGridLayout, QSplitter, QScrollArea, QFrame, QSystemTrayIcon)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QTime, QSize
from PySide6.QtGui import QImage, QPixmap, QFont, QColor

from core.window_capturer import WindowCapturer
from core.ocr_engine import OCREngine
from core.chat_deduplicator import ChatDeduplicator
from core.firebase_client import FirebaseClient
from core.web_push import WebPushManager
from core.boss_tracker import BossTracker

logger = logging.getLogger(__name__)

# ─── Premium Dark Theme QSS ───
DARK_THEME_QSS = """
/* ── Base ── */
QWidget {
    background-color: #0f1117;
    color: #e2e8f0;
    font-family: "Segoe UI", "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    font-size: 13px;
}

/* ── Tabs ── */
QTabWidget::pane {
    border: 1px solid #1e2533;
    background-color: #151821;
    border-radius: 10px;
    top: -1px;
}

QTabBar::tab {
    background-color: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    padding: 10px 20px;
    min-width: 90px;
    color: #6b7a99;
    font-size: 13px;
    font-weight: 600;
}

QTabBar::tab:selected {
    color: #7eb6ff;
    border-bottom-color: #5b9aff;
}

QTabBar::tab:hover:!selected {
    color: #a0b4d0;
    border-bottom-color: #394563;
}

/* ── GroupBox Cards ── */
QGroupBox {
    background-color: #161b26;
    border: 1px solid #1e2838;
    border-radius: 10px;
    margin-top: 18px;
    padding: 20px 14px 14px 14px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 2px 8px;
    color: #7eb6ff;
    font-size: 13px;
}

/* ── Buttons ── */
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #3b82f6;
}

QPushButton:pressed {
    background-color: #1d4ed8;
}

QPushButton:disabled {
    background-color: #2a3042;
    color: #4a5568;
}

QPushButton#btnDanger {
    background-color: #dc2626;
}
QPushButton#btnDanger:hover {
    background-color: #ef4444;
}
QPushButton#btnDanger:disabled {
    background-color: #2a3042;
    color: #4a5568;
}

QPushButton#btnSuccess {
    background-color: #16a34a;
}
QPushButton#btnSuccess:hover {
    background-color: #22c55e;
}

QPushButton#btnGhost {
    background-color: #1e2533;
    color: #a0b4d0;
    border: 1px solid #2a3550;
}
QPushButton#btnGhost:hover {
    background-color: #253048;
    color: #e2e8f0;
}

/* ── Inputs ── */
QComboBox, QSpinBox, QLineEdit, QTimeEdit {
    background-color: #131820;
    border: 1px solid #1e2838;
    border-radius: 8px;
    padding: 7px 10px;
    color: #e2e8f0;
    selection-background-color: #2563eb;
}

QComboBox:hover, QSpinBox:hover, QLineEdit:hover, QTimeEdit:hover {
    border-color: #2a3d5c;
}

QComboBox:focus, QSpinBox:focus, QLineEdit:focus, QTimeEdit:focus {
    border-color: #5b9aff;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

/* ── TextEdit / Console ── */
QTextEdit {
    background-color: #0c0f15;
    border: 1px solid #1e2533;
    border-radius: 8px;
    color: #94a3b8;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 12px;
    padding: 6px;
}

/* ── Labels ── */
QLabel {
    color: #94a3b8;
    background-color: transparent;
}

/* ── ListWidget ── */
QListWidget {
    background-color: #0f1319;
    border: 1px solid #1e2533;
    border-radius: 10px;
    padding: 4px;
    outline: none;
}

QListWidget::item {
    padding: 6px 8px;
    border-bottom: 1px solid #161d2a;
    border-radius: 6px;
}

QListWidget::item:hover {
    background-color: #171f2e;
}

QListWidget::item:selected {
    background-color: #1a2744;
    color: #e2e8f0;
}

/* ── CheckBox ── */
QCheckBox {
    color: #a0b4d0;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #2a3550;
    border-radius: 4px;
    background-color: #131820;
}

QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #5b9aff;
}

QCheckBox::indicator:hover {
    border-color: #5b9aff;
}

/* ── ScrollBar ── */
QScrollBar:vertical {
    background-color: transparent;
    width: 8px;
    margin: 4px 0;
}

QScrollBar::handle:vertical {
    background-color: #2a3550;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #3d5278;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* ── Splitter ── */
QSplitter::handle {
    background-color: #1e2533;
    height: 2px;
}

QSplitter::handle:hover {
    background-color: #5b9aff;
}

/* ── Frame Separator ── */
QFrame#separator {
    background-color: #1e2533;
    max-height: 1px;
}
"""

class ChatLogItemWidget(QWidget):
    def __init__(self, text, is_whitelisted, boss_name, whitelist_callback, blacklist_callback, edit_callback, parent=None):
        super().__init__(parent)
        self.text = text
        self.is_whitelisted = is_whitelisted
        self.boss_name = boss_name
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 3, 8, 3)
        layout.setSpacing(6)
        
        # Extract timestamp if present: "[HH:MM:SS] message"
        import re
        ts_match = re.match(r'^(\[\d{2}:\d{2}(:\d{2})?\])\s*(.*)$', text)
        if ts_match:
            ts_label = QLabel(ts_match.group(1))
            ts_label.setStyleSheet("color: #5b9aff; font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 12px; background: transparent;")
            ts_label.setFixedWidth(70)
            layout.addWidget(ts_label)
            self.content_text = ts_match.group(3)
        else:
            self.content_text = text

        # BOSS / Whitelist Badge Tag
        self.badge = QLabel()
        self.update_badge_style()
        layout.addWidget(self.badge)
            
        self.label = QLabel(self.content_text)
        self.update_label_style()
        self.label.setWordWrap(True)
        layout.addWidget(self.label, 1)

        # Action Buttons Layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        # Whitelist Button
        self.wl_btn = QPushButton()
        self.update_wl_button_style()
        self.wl_btn.clicked.connect(lambda: whitelist_callback(text, self))
        btn_layout.addWidget(self.wl_btn)

        # Blacklist (Exclude) Button
        self.ex_btn = QPushButton("❌ 排除")
        self.ex_btn.setToolTip("將此訊息加入黑名單並永久隱藏")
        self.ex_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e2533;
                border: 1px solid #7f1d1d;
                border-radius: 6px;
                color: #fca5a5;
                font-size: 11px;
                padding: 3px 8px;
            }
            QPushButton:hover {
                background-color: #dc2626;
                border-color: #ef4444;
                color: #ffffff;
            }
        """)
        self.ex_btn.clicked.connect(lambda: blacklist_callback(text))
        btn_layout.addWidget(self.ex_btn)

        # Edit/Correction Button
        self.edit_btn = QPushButton("✏️ 更正")
        self.edit_btn.setToolTip("手動更正此列辨識內容")
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e2533;
                border: 1px solid #2a3550;
                border-radius: 6px;
                color: #a0b4d0;
                font-size: 11px;
                padding: 3px 8px;
            }
            QPushButton:hover {
                background-color: #2563eb;
                border-color: #3b82f6;
                color: #ffffff;
            }
        """)
        self.edit_btn.clicked.connect(lambda: edit_callback(self))
        btn_layout.addWidget(self.edit_btn)

        layout.addLayout(btn_layout)

    def update_badge_style(self):
        if self.boss_name:
            self.badge.setText(f"[👾 BOSS: {self.boss_name}]")
            self.badge.setStyleSheet("color: #ffffff; background: #b45309; font-weight: bold; font-size: 11px; border-radius: 4px; padding: 1px 6px;")
            self.badge.setVisible(True)
        elif self.is_whitelisted:
            self.badge.setText("[★ 白名單]")
            self.badge.setStyleSheet("color: #ffffff; background: #78350f; font-weight: bold; font-size: 11px; border-radius: 4px; padding: 1px 6px;")
            self.badge.setVisible(True)
        else:
            self.badge.setVisible(False)

    def update_label_style(self):
        if self.boss_name or self.is_whitelisted:
            self.label.setStyleSheet("color: #fbbf24; font-size: 13px; font-weight: bold; background: transparent;")
        else:
            self.label.setStyleSheet("color: #94a3b8; font-size: 13px; background: transparent;")

    def update_wl_button_style(self):
        if self.is_whitelisted or self.boss_name:
            self.wl_btn.setText("★ 已標記")
            self.wl_btn.setToolTip("已在白名單或符合 BOSS 規則 (用以觸發 BOSS 計時)")
            self.wl_btn.setStyleSheet("""
                QPushButton {
                    background-color: #78350f;
                    border: 1px solid #d97706;
                    border-radius: 6px;
                    color: #fef3c7;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 3px 8px;
                }
            """)
        else:
            self.wl_btn.setText("⭐ 白名單")
            self.wl_btn.setToolTip("點擊將此訊息標記為白名單 (用以觸發 BOSS 計時)")
            self.wl_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1e2533;
                    border: 1px solid #d97706;
                    border-radius: 6px;
                    color: #fbbf24;
                    font-size: 11px;
                    padding: 3px 8px;
                }
                QPushButton:hover {
                    background-color: #b45309;
                    color: #ffffff;
                }
            """)

    def set_whitelisted(self, whitelisted=True, boss_name=None):
        self.is_whitelisted = whitelisted
        if boss_name is not None:
            self.boss_name = boss_name
        self.update_badge_style()
        self.update_label_style()
        self.update_wl_button_style()

class CaptureWorker(QThread):
    # Signals to communicate with UI
    log_signal = Signal(str)
    chat_log_signal = Signal(str, bool, str) # text, is_whitelisted, boss_name # text, is_whitelisted
    preview_signal = Signal(object) # Pass QPixmap or QImage
    boss_states_signal = Signal(dict)
    connection_status_signal = Signal(bool, str)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.running = False
        
        self.capturer = WindowCapturer()
        self.ocr_engine = OCREngine(lang=settings.get("ocr_lang", "zh-Hant"))
        self.deduplicator = ChatDeduplicator(threshold=settings.get("dedup_threshold", 0.75))
        self.firebase = FirebaseClient(settings.get("firebase_url"), settings.get("firebase_passcode"), api_key=settings.get("firebase_api_key"))
        self.web_push = WebPushManager(settings.get("vapid_private_key"))
        
        # Load boss rules
        self.boss_tracker = BossTracker(settings.get("boss_rules", []))
        
        # Update public VAPID key in settings
        self.settings["vapid_public_key"] = self.web_push.public_key_b64
        self.settings["vapid_private_key"] = self.web_push.private_key_pem
        
        # Buffer to keep chat history in memory (max 100 items)
        self.chat_history_buffer = []
        
        # Exact-match dedup cache: {cleaned_text: timestamp} to prevent same text showing twice
        self._recent_lines_cache = {}

    def update_settings(self, settings):
        self.settings = settings
        self.ocr_engine.lang = settings.get("ocr_lang", "zh-Hant")
        self.deduplicator.threshold = settings.get("dedup_threshold", 0.75)
        self.firebase.db_url = settings.get("firebase_url")
        self.firebase.passcode = settings.get("firebase_passcode")
        self.firebase.api_key = settings.get("firebase_api_key")
        self.boss_tracker.set_rules(settings.get("boss_rules", []))
        
        # Re-initialize web push if private key changed
        if self.web_push.private_key_pem != settings.get("vapid_private_key"):
            old_push = self.web_push
            self.web_push = WebPushManager(settings.get("vapid_private_key"))
            self.settings["vapid_public_key"] = self.web_push.public_key_b64
            self.settings["vapid_private_key"] = self.web_push.private_key_pem
            if old_push:
                old_push.close()

    def stop(self):
        self.running = False
        self.wait()
        self.capturer.close()

    def run(self):
        self.running = True
        self.log_signal.emit("背景監控執行緒已啟動（多視窗模式）...")

        # Sync configurations with Firebase once on startup
        self.sync_initial_config()

        ocr_interval = self.settings.get("ocr_interval_s", 2.0)
        
        last_ocr_time = 0
        last_report_check_time = 0
        last_ping_time = 0
        cycle_count = 0
        reported_window_count = -1
        self._last_fail_log_time = {} # Throttle capture failure logs per HWND

        try:
            while self.running:
                try:
                    now = time.time()
                    
                    # 1. OCR Capture & Processing (Interval-based)
                    if now - last_ocr_time >= ocr_interval:
                        last_ocr_time = now
                        cycle_count += 1
                        
                        # Auto-detect all game windows each cycle
                        windows = WindowCapturer.find_all_windows()
                        
                        if len(windows) != reported_window_count:
                            reported_window_count = len(windows)
                            if reported_window_count > 0:
                                titles = ', '.join([w['title'] for w in windows])
                                self.log_signal.emit(f"偵測到 {reported_window_count} 個遊戲視窗: {titles}")
                            else:
                                self.log_signal.emit("未偵測到任何遊戲視窗，等待視窗出現...")
                        
                        for win in windows:
                            if not self.running:
                                break
                            hwnd = win['hwnd']
                            if hwnd and win32gui.IsWindow(hwnd):
                                try:
                                    self.perform_ocr_cycle(hwnd)
                                except Exception as e:
                                    logger.error(f"Error in OCR cycle for HWND {hwnd}: {e}")

                        # Periodic garbage collection (every ~5 min)
                        if cycle_count % 150 == 0:
                            import gc
                            gc.collect()

                    # 2. Check for Manual Reports (Every 2 seconds)
                    if now - last_report_check_time >= 2.0:
                        last_report_check_time = now
                        if self.firebase.is_configured():
                            try:
                                self.process_incoming_firebase_events()
                            except Exception as e:
                                logger.error(f"Error during Firebase report processing: {e}")

                    # 3. Connection Ping & Status Update (Every 30 seconds to avoid blocking OCR loop)
                    if now - last_ping_time >= 30.0:
                        last_ping_time = now
                        if self.firebase.is_configured():
                            try:
                                success, msg = self.firebase.test_connection()
                                self.connection_status_signal.emit(success, msg)
                            except Exception as e:
                                logger.error(f"Error during Firebase status ping: {e}")
                        else:
                            self.connection_status_signal.emit(False, "未設定 Firebase 連線")
                except Exception as outer_e:
                    logger.error(f"Unexpected error in CaptureWorker loop: {outer_e}")

                # Sleep short time to prevent maxing out CPU
                time.sleep(0.1)
        finally:
            if hasattr(self, "capturer") and self.capturer:
                try:
                    self.capturer.close()
                except Exception:
                    pass
            self.log_signal.emit("背景監控執行緒已停止。")

    def sync_initial_config(self):
        """Publish VAPID public key and initial states to Firebase Realtime Database."""
        if not self.firebase.is_configured():
            return
        
        # Upload public key
        url = self.firebase._get_url("vapid_public_key")
        try:
            self.firebase.session.put(url, json=self.web_push.public_key_b64, timeout=5)
            logger.info("Uploaded VAPID Public Key to Firebase successfully.")
        except Exception as e:
            logger.error(f"Failed to upload public key to Firebase: {e}")

        # Synchronize remote boss states from Firebase DB on startup
        db_states = self.firebase.get_boss_states()
        if db_states:
            if self.boss_tracker.update_states_from_db(db_states):
                logger.info("Successfully synchronized remote BOSS states from Firebase DB.")
                self.boss_states_signal.emit(self.boss_tracker.states)
        else:
            # If DB has no states yet, upload local initial boss states
            self.firebase.update_boss_states(self.boss_tracker.states)

        self.firebase.update_boss_rules(self.settings.get("boss_rules", []))

    def perform_ocr_cycle(self, hwnd):
        # Coordinates (X, Y, W, H) relative to client area
        rx = self.settings.get("crop_x", 20)
        ry = self.settings.get("crop_y", 500)
        rw = self.settings.get("crop_w", 400)
        rh = self.settings.get("crop_h", 180)
        region = (rx, ry, rw, rh)

        # Capture
        frame = self.capturer.capture_client_area(hwnd, region)
        if frame is not None:
            # Run OCR
            threshold_val = self.settings.get("ocr_threshold", 150)
            
            ocr_res = self.ocr_engine.recognize_text(
                frame, 
                threshold_val=threshold_val, 
                scale=2, 
                use_binarization=self.settings.get("use_binarization", False),
                use_yellow_filter=self.settings.get("use_yellow_filter", True)
            )
            raw_lines = ocr_res.get("lines", [])
            
            if raw_lines:
                # Deduplicate
                new_lines = self.deduplicator.add_lines(raw_lines)
                if new_lines:
                    self.process_new_chat_lines(new_lines)
        else:
            # Throttle failure logging per HWND (log at most once every 60 seconds)
            now_ts = time.time()
            last_log = getattr(self, "_last_fail_log_time", {}).get(hwnd, 0)
            if now_ts - last_log > 60:
                if not hasattr(self, "_last_fail_log_time"):
                    self._last_fail_log_time = {}
                self._last_fail_log_time[hwnd] = now_ts
                self.log_signal.emit(f"視窗 [HWND:{hwnd}] 擷圖失敗，請確認遊戲未最小化！")

    def clean_ocr_time_word(self, word):
        """
        Cleans OCR time string mismatches like l9:25, 20o1, [19.25] to standard 19:25.
        """
        # Remove brackets and punctuation from ends
        w = word.strip("[]()〔〕{}<>.,:：-_ ")
        
        # Replace common digit OCR mismatches
        char_map = {
            'l': '1', 'I': '1', '|': '1', '/': '1', '\\': '1', '!': '1', 'i': '1', '临': '1', '¡': '1', 'j': '1', 'J': '1',
            'F': '1', 't': '1', 'T': '1', 'r': '1', 'Y': '1', 'f': '1',
            'o': '0', 'O': '0', 'D': '0', 'Q': '0',
            'z': '2', 'Z': '2',
            's': '5', 'S': '5',
            'b': '6', 'G': '6',
            'g': '9', 'q': '9'
        }
        
        cleaned = []
        for char in w:
            if char in char_map:
                cleaned.append(char_map[char])
            elif char.isdigit() or char in '.:：':
                cleaned.append(char)
                
        return "".join(cleaned)

    def parse_line_timestamp(self, line, reference_time):
        """
        Parses a timestamp like [12:34], [12:34:56], 12:34 from the line.
        Supports OCR correcting logic to ensure robustness.
        Returns: (cleaned_line, parsed_datetime)
        """
        import re
        from datetime import datetime, time, timedelta

        # Strip trailing punctuation/spaces first
        line_str = line.strip().rstrip("[]()〔〕{}<>.,:：-_ ")
        parts = line_str.split()
        if not parts:
            return line, reference_time

        # Extract the last word as the primary timestamp candidate
        last_word = parts[-1]
        cleaned_last_word = self.clean_ocr_time_word(last_word)
        
        # Reconstruct the line with the cleaned time word for matching
        cleaned_line_for_matching = " ".join(parts[:-1] + [cleaned_last_word])

        # 1. Try matching at the end of the line (separator is optional here to handle OCR omissions)
        pattern_end = r'(?:\[|\b)(\d{2})[\s\.:：\-\—]?(\d{2})(?:\]|\b)\s*$'
        match = re.search(pattern_end, cleaned_line_for_matching)
        
        # 2. If no match at end, try matching anywhere but require a separator to avoid false matches
        if not match:
            pattern_any = r'(?:\[|\b)(\d{2})[\s\.:：\-\—]+(\d{2})(?:\]|\b)'
            match = re.search(pattern_any, cleaned_line_for_matching)
        
        if match:
            try:
                h = int(match.group(1))
                m = int(match.group(2))
                s = 0
                
                if 0 <= h < 24 and 0 <= m < 60:
                    # Construct datetime on the reference day
                    msg_dt = datetime.combine(reference_time.date(), time(h, m, s))
                    
                    # Handle midnight rollover (if message time is in future relative to reference_time)
                    if msg_dt > reference_time + timedelta(minutes=30):
                        msg_dt -= timedelta(days=1)
                        
# Remove the original last word (the timestamp) from the line
                    original_clean_parts = parts[:-1]
                    cleaned_line = " ".join(original_clean_parts)
                    
                    # Clean up residual characters at the start/end of the line
                    cleaned_line = re.sub(r'^[\s\]\[:：\-\—]+', '', cleaned_line)
                    cleaned_line = re.sub(r'[\s\]\[:：\-\—]+$', '', cleaned_line).strip()
                    
                    return cleaned_line, msg_dt
            except Exception as e:
                logger.error(f"Error parsing timestamp from line '{line}': {e}")
                
        return line, reference_time

    def process_new_chat_lines(self, lines):
        """Append timestamps to new lines, update UI, and parse boss rules for whitelisted/boss lines."""
        now_dt = datetime.now()
        
        formatted_lines = []
        parsed_events = [] # List of tuples: (cleaned_line, event_time, is_whitelisted)
        
        for line in lines:
            cleaned_line, event_time = self.parse_line_timestamp(line, now_dt)
            if not cleaned_line:
                continue
            
            # Apply user-trained auto-corrections if there's an exact match
            corrections = self.settings.get("ocr_corrections", {})
            if cleaned_line in corrections:
                old_cleaned = cleaned_line
                cleaned_line = corrections[cleaned_line]
                logger.info(f"Auto-correcting OCR output: '{old_cleaned}' -> '{cleaned_line}'")
            
            # 1. WHITELIST & BOSS RULE CHECK FIRST (Whitelisted / Boss lines are never accidentally blacklisted)
            whitelisted_list = self.settings.get("whitelisted_messages", [])
            tracker = self.boss_tracker if hasattr(self, "boss_tracker") else BossTracker(self.settings.get("boss_rules", []))
            
            matched_boss_name = tracker.get_matched_boss_name(cleaned_line)
            contains_boss_name = tracker.contains_any_boss_name(cleaned_line) if hasattr(tracker, "contains_any_boss_name") else False
            is_whitelisted = (cleaned_line in whitelisted_list) or (matched_boss_name is not None) or contains_boss_name

            # 2. BLACKLIST CHECK: If line is NOT whitelisted/boss, check wildcard/pattern exclusions
            if not is_whitelisted:
                exclusions = self.settings.get("excluded_messages", [])
                if self.is_blacklisted_line(cleaned_line, exclusions):
                    logger.info(f"Skipping blacklisted message: '{cleaned_line}'")
                    continue

            # Exact-match dedup: skip if this exact text was already seen recently (within 30s)
            now_ts = time.time()
            if cleaned_line in self._recent_lines_cache:
                if now_ts - self._recent_lines_cache[cleaned_line] < 30:
                    continue
            self._recent_lines_cache[cleaned_line] = now_ts
            
            # Periodically prune expired entries from cache
            if len(self._recent_lines_cache) > 200:
                cutoff = now_ts - 30
                self._recent_lines_cache = {k: v for k, v in self._recent_lines_cache.items() if v > cutoff}
            
            timestamp_str = event_time.strftime("%H:%M:%S")
            formatted_line = f"[{timestamp_str}] {cleaned_line}"
            
            formatted_lines.append(formatted_line)
            parsed_events.append((cleaned_line, event_time, is_whitelisted))
            
            # Emit line to UI along with its whitelisted status and matched boss name
            self.chat_log_signal.emit(formatted_line, is_whitelisted, matched_boss_name or "")
            
            # Accumulate in memory buffer (hard-bounded to the last 100 entries)
            self.chat_history_buffer.append(formatted_line)
            if len(self.chat_history_buffer) > 100:
                del self.chat_history_buffer[:-100]

    @staticmethod
    def is_blacklisted_line(line, exclusions):
        """Check if line matches exact string, substring, or wildcard pattern (*, ?) in exclusions."""
        if not line:
            return False
        clean_strip = str(line).strip()
        if len(clean_strip) < 2:
            return True
            
        if not exclusions:
            return False
            
        import fnmatch
        for exc in exclusions:
            if not exc:
                continue
            exc_str = str(exc).strip()
            # Wildcard pattern (e.g. "*得*", "*卡片*", "*1個*")
            if "*" in exc_str or "?" in exc_str:
                if fnmatch.fnmatch(clean_strip, exc_str):
                    return True
            else:
                # Substring or exact match
                if exc_str in clean_strip:
                    return True
        return False

    def process_incoming_firebase_events(self):
        """Fetch pending manual reports and test push requests from Firebase."""
        reports = self.firebase.get_reports()
        if not reports:
            return

        state_changed = False
        
        for report_id, report_data in list(reports.items()):
            # Check if it is a test push request
            if report_data.get("type") == "test_push":
                device_id = report_data.get("device_id")
                self.log_signal.emit(f"收到來自裝置 {device_id} 的推播測試請求...")
                
                # Fetch target subscriber token
                subs = self.firebase.get_subscriptions()
                target_sub = subs.get(device_id)
                
                if target_sub:
                    self.web_push.send_notification(target_sub, "🔔 測試推播", "王怪計時器連線成功！您將在此收到即時警報。")
                    self.log_signal.emit(f"已發送測試推播給裝置 {device_id}")
                else:
                    self.log_signal.emit(f"發送測試推播失敗：找不到該裝置的訂閱資訊。")
                
                self.firebase.delete_report(report_id)
                continue

            # Check passcode logic
            passcode = report_data.get("passcode")
            if passcode != self.firebase.passcode:
                # Invalid passcode, discard
                self.firebase.delete_report(report_id)
                continue

            # Process manual death report
            boss_name = report_data.get("boss_name")
            reporter = report_data.get("reported_by", "Guest")
            
            self.log_signal.emit(f"處理手動通報: {reporter} 通報 {boss_name} 死亡")
            
            event = self.boss_tracker.process_manual_report(report_data)
            if event:
                state_changed = True
                # Trigger push notification to other members
                title = f"👹 手動通報王死: {boss_name}"
                body = f"{reporter} 通報 {boss_name} 已死亡。下次重生：{event['next_spawn']}"
                self.broadcast_push_notification(title, body)

            # Clear report
            self.firebase.delete_report(report_id)

        if state_changed:
            self.firebase.update_boss_states(self.boss_tracker.states)
            self.boss_states_signal.emit(self.boss_tracker.states)

    def broadcast_push_notification(self, title, body):
        """Send Web Push to all active subscriptions in Firebase."""
        subs = self.firebase.get_subscriptions()
        if not subs:
            return

        def on_expired(sub_id):
            # Delete expired tokens from database to keep subscriptions clean
            url = self.firebase._get_url(f"subscriptions/{sub_id}")
            if url:
                try:
                    self.firebase.session.delete(url, timeout=3)
                    self.log_signal.emit(f"清理已失效的手機訂閱憑證: {sub_id}")
                except Exception:
                    pass

        self.log_signal.emit(f"正在廣播推播至 {len(subs)} 個手機用戶...")
        success_c, fail_c = self.web_push.send_to_all(subs, title, body, expired_callback=on_expired)
        self.log_signal.emit(f"推播廣播完成：{success_c} 成功, {fail_c} 失敗。")


class MainWindow(QWidget):
    def __init__(self, settings_path="config/settings.json"):
        super().__init__()
        self.settings_path = settings_path
        self.settings = self.load_settings()
        self.worker = None

        self.setWindowTitle("天堂W 對話擷取與 BOSS 監控")
        self.resize(1060, 760)
        self.setStyleSheet(DARK_THEME_QSS)

        from PySide6.QtGui import QIcon
        if os.path.exists("icons/logo.jpg"):
            app_icon = QIcon("icons/logo.jpg")
            self.setWindowIcon(app_icon)

        self.init_ui()
        self.refresh_windows()
        self.populate_rules_list()
        self.sync_boss_states_from_db()

        # Initialize Windows Native System Tray Icon for bottom-right toast notifications
        self.tray_icon = QSystemTrayIcon(self)
        if os.path.exists("icons/logo.jpg"):
            self.tray_icon.setIcon(QIcon("icons/logo.jpg"))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray_icon.show()

        # Update preview timer (for when running)
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.request_preview_update)

    def show_windows_toast(self, title, message):
        """Display native Windows bottom-right notification toast."""
        if hasattr(self, 'tray_icon') and self.tray_icon and QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.showMessage(
                title,
                message,
                QSystemTrayIcon.Information,
                5000  # 5 seconds duration
            )

    def sync_boss_states_from_db(self):
        """Fetch remote boss states from Firebase Realtime Database on startup."""
        url = self.settings.get("firebase_url")
        passcode = self.settings.get("firebase_passcode")
        if url:
            try:
                fb = FirebaseClient(url, passcode)
                db_states = fb.get_boss_states()
                if db_states:
                    tracker = BossTracker(self.settings.get("boss_rules", []))
                    if tracker.update_states_from_db(db_states):
                        self.update_boss_ui(tracker.states)
                        self.log_message("🎉 成功從 Firebase 資料庫讀取並同步全數 BOSS 時間狀態！")
            except Exception as e:
                logger.error(f"Failed to sync boss states from DB on startup: {e}")

    def sanitize_corrections(self, corrections_dict):
        """Sanitizes corrections dict by stripping any timestamps from keys and values."""
        sanitized = {}
        for k, v in corrections_dict.items():
            clean_k = re.sub(r'^\[\d{2}:\d{2}(:\d{2})?\]\s*', '', k).strip()
            clean_v = re.sub(r'^\[\d{2}:\d{2}(:\d{2})?\]\s*', '', v).strip()
            if clean_k and clean_v:
                sanitized[clean_k] = clean_v
        return sanitized

    def load_settings(self):
        settings = {}
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except Exception:
                pass
        
        if settings:
            if "ocr_corrections" in settings:
                settings["ocr_corrections"] = self.sanitize_corrections(settings["ocr_corrections"])
            return settings

        # Defaults
        return {
            "hwnd": None,
            "crop_x": 20,
            "crop_y": 500,
            "crop_w": 400,
            "crop_h": 180,
            "only_boss_messages": True,
            "use_yellow_filter": True,
            "use_binarization": False,
            "ocr_threshold": 150,
            "ocr_interval_s": 2.0,
            "dedup_threshold": 0.75,
            "ocr_lang": "zh-Hant",
            "firebase_url": "",
            "firebase_passcode": "7777",
            "vapid_private_key": None,
            "vapid_public_key": None,
            "boss_rules": [
                {
                    "name": "卡士伯",
                    "spawn_keywords": ["卡士伯", "出現"],
                    "death_keywords": ["卡士伯", "擊敗"],
                    "cooldown_mins": 120
                },
                {
                    "name": "巴風特",
                    "spawn_keywords": ["巴風特", "出現"],
                    "death_keywords": ["巴風特", "擊敗"],
                    "cooldown_mins": 120
                }
            ]
        }

    def save_settings(self):
        os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            self.write_pwa_firebase_config()
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def write_pwa_firebase_config(self):
        """Export current Firebase URL & Passcode to data/firebase_config.json for static hosting & GitHub Pages."""
        try:
            data = {
                "databaseURL": self.settings.get("firebase_url", ""),
                "passcode": self.settings.get("firebase_passcode", "123456789")
            }
            # Root data dir
            root_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            os.makedirs(root_data_dir, exist_ok=True)
            with open(os.path.join(root_data_dir, "firebase_config.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Web subfolder data dir
            web_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "data")
            os.makedirs(web_data_dir, exist_ok=True)
            with open(os.path.join(web_data_dir, "firebase_config.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info("Exported data/firebase_config.json successfully.")
        except Exception as e:
            logger.error(f"Failed to write data/firebase_config.json: {e}")

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 10, 12, 10)
        root_layout.setSpacing(8)

        # ══════════════════════════════════════════
        # ═ TOP CONTROL BAR
        # ══════════════════════════════════════════
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        # App title
        title_lbl = QLabel("🎮 天堂W BOSS 監控")
        title_lbl.setStyleSheet("color: #e2e8f0; font-size: 18px; font-weight: bold; background: transparent;")
        top_bar.addWidget(title_lbl)

        top_bar.addStretch()

        # Firebase status indicator
        self.fb_status_lbl = QLabel("● 未連線")
        self.fb_status_lbl.setStyleSheet("color: #4a5568; font-size: 12px; font-weight: bold; background: transparent;")
        top_bar.addWidget(self.fb_status_lbl)

        # Separator dot
        sep = QLabel("│")
        sep.setStyleSheet("color: #2a3550; background: transparent;")
        top_bar.addWidget(sep)

        # Control buttons
        self.start_btn = QPushButton("▶  啟動監控")
        self.start_btn.setObjectName("btnSuccess")
        self.start_btn.setFixedHeight(36)
        self.start_btn.clicked.connect(self.start_monitoring)
        top_bar.addWidget(self.start_btn)

        self.stop_btn = QPushButton("■  停止")
        self.stop_btn.setObjectName("btnDanger")
        self.stop_btn.setFixedHeight(36)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_monitoring)
        top_bar.addWidget(self.stop_btn)

        self.test_ocr_btn = QPushButton("🔍 測試辨識")
        self.test_ocr_btn.setObjectName("btnGhost")
        self.test_ocr_btn.setFixedHeight(36)
        self.test_ocr_btn.clicked.connect(self.test_single_ocr)
        top_bar.addWidget(self.test_ocr_btn)

        root_layout.addLayout(top_bar)

        # Thin separator line
        sep_line = QFrame()
        sep_line.setObjectName("separator")
        sep_line.setFrameShape(QFrame.HLine)
        root_layout.addWidget(sep_line)

        # ══════════════════════════════════════════
        # ═ MAIN CONTENT SPLITTER (Tabs + Bottom Panel)
        # ══════════════════════════════════════════
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(3)

        # ── TABS ──
        self.tabs = QTabWidget()

        # ─── Tab 1: 💬 對話紀錄 ───
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(8, 8, 8, 8)
        chat_layout.setSpacing(6)

        tip_label = QLabel("💡 雙擊任意一列可「手動更正」辨識內容，更正後將重算 BOSS 計時")
        tip_label.setStyleSheet("color: #4a6080; font-size: 11px; background: transparent; padding: 2px 0;")
        chat_layout.addWidget(tip_label)

        self.chat_edit = QListWidget()
        self.chat_edit.itemDoubleClicked.connect(self.correct_chat_message)
        chat_layout.addWidget(self.chat_edit)

        clear_chat_btn = QPushButton("清除畫面")
        clear_chat_btn.setObjectName("btnGhost")
        clear_chat_btn.clicked.connect(self.clear_chat_list)
        chat_layout.addWidget(clear_chat_btn)
        self.tabs.addTab(chat_widget, "💬 對話紀錄")

        # ─── Tab 2: 👹 王怪計時 ───
        boss_widget = QWidget()
        boss_outer_layout = QVBoxLayout(boss_widget)
        boss_outer_layout.setContentsMargins(8, 8, 8, 8)
        boss_outer_layout.setSpacing(10)

        # Scrollable card grid area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.boss_cards_container = QWidget()
        self.boss_cards_container.setStyleSheet("background: transparent;")
        self.boss_cards_layout = QGridLayout(self.boss_cards_container)
        self.boss_cards_layout.setSpacing(10)
        self.boss_cards_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self.boss_cards_container)
        boss_outer_layout.addWidget(scroll, 1)

        # Boss manual correction controls
        correction_group = QGroupBox("手動校正")
        correction_layout = QVBoxLayout(correction_group)
        correction_layout.setSpacing(8)

        # Custom time row
        time_row = QHBoxLayout()
        self.use_custom_death_time_chk = QCheckBox("自訂死亡時間")
        self.custom_death_time = QTimeEdit()
        self.custom_death_time.setDisplayFormat("HH:mm")
        self.custom_death_time.setTime(QTime.currentTime())
        self.custom_death_time.setEnabled(False)
        self.use_custom_death_time_chk.toggled.connect(self.custom_death_time.setEnabled)
        time_row.addWidget(self.use_custom_death_time_chk)
        time_row.addWidget(self.custom_death_time)
        time_row.addStretch()
        correction_layout.addLayout(time_row)

        # Boss action row
        action_row = QHBoxLayout()
        self.correct_boss_combo = QComboBox()
        self.correct_boss_combo.setMinimumWidth(140)
        correct_alive_btn = QPushButton("強制存活")
        correct_alive_btn.setObjectName("btnSuccess")
        correct_dead_btn = QPushButton("強制死亡")
        correct_dead_btn.setObjectName("btnDanger")
        action_row.addWidget(QLabel("選擇 BOSS:"))
        action_row.addWidget(self.correct_boss_combo, 1)
        action_row.addWidget(correct_alive_btn)
        action_row.addWidget(correct_dead_btn)
        correct_alive_btn.clicked.connect(self.force_boss_alive)
        correct_dead_btn.clicked.connect(self.force_boss_dead)
        correction_layout.addLayout(action_row)

        boss_outer_layout.addWidget(correction_group)
        self.tabs.addTab(boss_widget, "👹 BOSS 計時")

        # ─── Tab 3: ⚙️ 系統設定（合併原左欄設定）───
        config_widget = QWidget()
        config_scroll = QScrollArea()
        config_scroll.setWidgetResizable(True)
        config_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        config_inner = QWidget()
        config_inner.setStyleSheet("background: transparent;")
        config_layout = QVBoxLayout(config_inner)
        config_layout.setSpacing(12)
        config_layout.setContentsMargins(8, 8, 8, 8)

        # Section A: Window Binding
        bind_group = QGroupBox("🎮 遊戲視窗綁定")
        bind_layout = QHBoxLayout(bind_group)
        bind_layout.setSpacing(8)
        self.win_combo = QComboBox()
        self.win_combo.setSizePolicy(self.win_combo.sizePolicy())
        self.refresh_btn = QPushButton("重新整理")
        self.refresh_btn.setObjectName("btnGhost")
        self.refresh_btn.clicked.connect(self.refresh_windows)
        self.bind_btn = QPushButton("綁定視窗")
        self.bind_btn.clicked.connect(self.bind_window)
        bind_layout.addWidget(QLabel("選擇視窗:"))
        bind_layout.addWidget(self.win_combo, 1)
        bind_layout.addWidget(self.refresh_btn)
        bind_layout.addWidget(self.bind_btn)
        config_layout.addWidget(bind_group)

        # Section B: Crop Settings
        crop_group = QGroupBox("📐 擷取範圍微調")
        crop_grid = QGridLayout(crop_group)
        crop_grid.setSpacing(10)

        self.spin_x = QSpinBox()
        self.spin_x.setRange(0, 2000)
        self.spin_x.setValue(self.settings.get("crop_x", 20))
        self.spin_y = QSpinBox()
        self.spin_y.setRange(0, 2000)
        self.spin_y.setValue(self.settings.get("crop_y", 500))
        self.spin_w = QSpinBox()
        self.spin_w.setRange(50, 2000)
        self.spin_w.setValue(self.settings.get("crop_w", 400))
        self.spin_h = QSpinBox()
        self.spin_h.setRange(20, 2000)
        self.spin_h.setValue(self.settings.get("crop_h", 180))

        crop_grid.addWidget(QLabel("X 座標:"), 0, 0)
        crop_grid.addWidget(self.spin_x, 0, 1)
        crop_grid.addWidget(QLabel("Y 座標:"), 0, 2)
        crop_grid.addWidget(self.spin_y, 0, 3)
        crop_grid.addWidget(QLabel("寬度:"), 1, 0)
        crop_grid.addWidget(self.spin_w, 1, 1)
        crop_grid.addWidget(QLabel("高度:"), 1, 2)
        crop_grid.addWidget(self.spin_h, 1, 3)

        self.spin_x.valueChanged.connect(self.update_crop_settings)
        self.spin_y.valueChanged.connect(self.update_crop_settings)
        self.spin_w.valueChanged.connect(self.update_crop_settings)
        self.spin_h.valueChanged.connect(self.update_crop_settings)
        config_layout.addWidget(crop_group)

        # Section C: Firebase
        fb_group = QGroupBox("☁️ Firebase 雲端同步")
        fb_vbox = QVBoxLayout(fb_group)
        fb_vbox.setSpacing(8)
        self.fb_url_edit = QLineEdit(self.settings.get("firebase_url", ""))
        self.fb_url_edit.setPlaceholderText("https://xxxx-default-rtdb.firebaseio.com")
        self.fb_pass_edit = QLineEdit(self.settings.get("firebase_passcode", "7777"))
        self.fb_pass_edit.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.fb_pass_edit.setPlaceholderText("血盟暗號 / 密碼")
        self.fb_api_key_edit = QLineEdit(self.settings.get("firebase_api_key", ""))
        self.fb_api_key_edit.setPlaceholderText("Firebase Web API Key (AIzaSy... 用於匿名認證，選用)")
        self.fb_appcheck_edit = QLineEdit(self.settings.get("firebase_appcheck_token", ""))
        self.fb_appcheck_edit.setPlaceholderText("Firebase App Check Token / reCAPTCHA v3 Site Key (選用)")
        
        test_fb_btn = QPushButton("⚡  測試 Firebase 連線")
        test_fb_btn.setObjectName("btnGhost")
        test_fb_btn.clicked.connect(lambda: self.test_firebase_connection_from_ui(show_popup=True))

        fb_vbox.addWidget(QLabel("Database URL:"))
        fb_vbox.addWidget(self.fb_url_edit)
        fb_vbox.addWidget(QLabel("血盟暗號 (Passcode):"))
        fb_vbox.addWidget(self.fb_pass_edit)
        fb_vbox.addWidget(QLabel("Firebase Web API Key (匿名認證):"))
        fb_vbox.addWidget(self.fb_api_key_edit)
        fb_vbox.addWidget(QLabel("App Check Token / Site Key (選用):"))
        fb_vbox.addWidget(self.fb_appcheck_edit)
        fb_vbox.addWidget(test_fb_btn)
        config_layout.addWidget(fb_group)

        # Section D: OCR Settings
        ocr_group = QGroupBox("🔤 OCR 辨識設定")
        ocr_vbox = QVBoxLayout(ocr_group)
        ocr_vbox.setSpacing(8)

        self.only_boss_messages_chk = QCheckBox("僅記錄 BOSS 相關訊息（白名單模式，只顯示符合 BOSS 關鍵字之公告，其餘雜訊自動過濾）")
        self.only_boss_messages_chk.setChecked(self.settings.get("only_boss_messages", True))

        self.use_yellow_filter_chk = QCheckBox("啟用黃色系統字過濾（推薦，過濾掉一般玩家聊天）")
        self.use_yellow_filter_chk.setChecked(self.settings.get("use_yellow_filter", True))

        self.use_binarization_chk = QCheckBox("啟用二值化去色（進階調校用，一般無須勾選）")
        self.use_binarization_chk.setChecked(self.settings.get("use_binarization", False))

        self.ocr_threshold_spin = QSpinBox()
        self.ocr_threshold_spin.setRange(50, 240)
        self.ocr_threshold_spin.setValue(self.settings.get("ocr_threshold", 150))

        self.ocr_interval_spin = QSpinBox()
        self.ocr_interval_spin.setRange(1, 10)
        self.ocr_interval_spin.setValue(int(self.settings.get("ocr_interval_s", 2)))

        self.ocr_lang_combo = QComboBox()

        ocr_vbox.addWidget(self.only_boss_messages_chk)
        ocr_vbox.addWidget(self.use_yellow_filter_chk)
        ocr_vbox.addWidget(self.use_binarization_chk)

        ocr_grid = QGridLayout()
        ocr_grid.setSpacing(8)
        ocr_grid.addWidget(QLabel("二值化閾值 (50-240):"), 0, 0)
        ocr_grid.addWidget(self.ocr_threshold_spin, 0, 1)
        ocr_grid.addWidget(QLabel("偵測間隔 (秒):"), 0, 2)
        ocr_grid.addWidget(self.ocr_interval_spin, 0, 3)
        ocr_grid.addWidget(QLabel("辨識語言:"), 1, 0)
        ocr_grid.addWidget(self.ocr_lang_combo, 1, 1, 1, 3)
        ocr_vbox.addLayout(ocr_grid)
        config_layout.addWidget(ocr_group)

        # Save Config Button
        save_cfg_btn = QPushButton("💾  儲存所有設定")
        save_cfg_btn.setFixedHeight(40)
        save_cfg_btn.clicked.connect(self.save_config_from_ui)
        config_layout.addWidget(save_cfg_btn)

        config_layout.addStretch()
        config_scroll.setWidget(config_inner)
        config_outer_layout = QVBoxLayout(config_widget)
        config_outer_layout.setContentsMargins(0, 0, 0, 0)
        config_outer_layout.addWidget(config_scroll)
        self.tabs.addTab(config_widget, "⚙️ 系統設定")

        # ─── Tab 4: 📝 BOSS 規則設定 ───
        rules_widget = QWidget()
        rules_layout = QHBoxLayout(rules_widget)
        rules_layout.setSpacing(12)
        rules_layout.setContentsMargins(8, 8, 8, 8)

        # Left - Boss List
        list_group = QGroupBox("BOSS 清單")
        list_vbox = QVBoxLayout(list_group)
        self.rules_list = QListWidget()
        self.rules_list.itemClicked.connect(self.load_boss_rule_details)
        list_vbox.addWidget(self.rules_list)
        rules_layout.addWidget(list_group, 1)

        # Right - Edit Form
        edit_group = QGroupBox("編輯規則")
        edit_vbox = QVBoxLayout(edit_group)
        edit_vbox.setSpacing(10)

        self.rule_name_edit = QLineEdit()
        self.rule_name_edit.setPlaceholderText("例如：巴風特 / 克特")
        
        self.rule_type_combo = QComboBox()
        self.rule_type_combo.addItem("⏱️ 週期王 (擊殺後 CD 計時)", "cooldown")
        self.rule_type_combo.addItem("📅 固定時間王 (每日 / 指定星期與時段)", "fixed")
        
        self.rule_spawn_edit = QLineEdit()
        self.rule_spawn_edit.setPlaceholderText("逗號分隔，例如：巴風特, 出現")
        self.rule_death_edit = QLineEdit()
        self.rule_death_edit.setPlaceholderText("逗號分隔，例如：巴風特, 擊")

        # Container for Cooldown SpinBox
        self.cooldown_container = QWidget()
        cooldown_lay = QVBoxLayout(self.cooldown_container)
        cooldown_lay.setContentsMargins(0, 0, 0, 0)
        self.rule_cooldown_spin = QSpinBox()
        self.rule_cooldown_spin.setRange(1, 10080)
        self.rule_cooldown_spin.setValue(120)
        cooldown_lay.addWidget(QLabel("計時 CD 時間 (分鐘):"))
        cooldown_lay.addWidget(self.rule_cooldown_spin)

        # Container for Fixed Schedule Options
        self.fixed_container = QWidget()
        fixed_lay = QVBoxLayout(self.fixed_container)
        fixed_lay.setContentsMargins(0, 0, 0, 0)
        fixed_lay.setSpacing(6)
        
        fixed_lay.addWidget(QLabel("固定出生星期 (選取發動日期，不勾選則預設每日):"))
        days_hb = QHBoxLayout()
        days_hb.setSpacing(6)
        self.day_checkboxes = []
        # Mon=1, Tue=2, Wed=3, Thu=4, Fri=5, Sat=6, Sun=0
        day_items = [("一", 1), ("二", 2), ("三", 3), ("四", 4), ("五", 5), ("六", 6), ("日", 0)]
        for label, day_num in day_items:
            chk = QCheckBox(label)
            chk.setChecked(True)
            chk.setProperty("day_num", day_num)
            days_hb.addWidget(chk)
            self.day_checkboxes.append(chk)

        self.btn_select_all_days = QPushButton("全選/每日")
        self.btn_select_all_days.setFixedHeight(24)
        self.btn_select_all_days.clicked.connect(self.toggle_all_day_checkboxes)
        days_hb.addWidget(self.btn_select_all_days)
        fixed_lay.addLayout(days_hb)

        fixed_lay.addWidget(QLabel("固定出生時段 24H (逗號分隔多個時間，例如：18:00, 22:00):"))
        self.rule_fixed_times_edit = QLineEdit()
        self.rule_fixed_times_edit.setPlaceholderText("例如：18:00, 22:00")
        fixed_lay.addWidget(self.rule_fixed_times_edit)

        self.rule_type_combo.currentIndexChanged.connect(self.on_rule_type_changed)
        self.fixed_container.setVisible(False)

        edit_vbox.addWidget(QLabel("BOSS 名稱:"))
        edit_vbox.addWidget(self.rule_name_edit)
        edit_vbox.addWidget(QLabel("頭目類型:"))
        edit_vbox.addWidget(self.rule_type_combo)
        edit_vbox.addWidget(QLabel("重生關鍵字 (逗號分隔):"))
        edit_vbox.addWidget(self.rule_spawn_edit)
        edit_vbox.addWidget(QLabel("死亡關鍵字 (逗號分隔):"))
        edit_vbox.addWidget(self.rule_death_edit)
        edit_vbox.addWidget(self.cooldown_container)
        edit_vbox.addWidget(self.fixed_container)

        btn_layout = QHBoxLayout()
        add_update_btn = QPushButton("新增 / 更新")
        add_update_btn.clicked.connect(self.add_or_update_boss_rule)
        delete_btn = QPushButton("刪除 BOSS")
        delete_btn.setObjectName("btnDanger")
        delete_btn.clicked.connect(self.delete_boss_rule)
        btn_layout.addWidget(add_update_btn)
        btn_layout.addWidget(delete_btn)
        edit_vbox.addLayout(btn_layout)

        save_rules_btn = QPushButton("💾  儲存所有 BOSS 設定")
        save_rules_btn.clicked.connect(self.save_boss_rules_to_settings)
        edit_vbox.addWidget(save_rules_btn)

        edit_vbox.addStretch()
        rules_layout.addWidget(edit_group, 2)
        self.tabs.addTab(rules_widget, "📝 BOSS 規則設定")

        splitter.addWidget(self.tabs)

        # ══════════════════════════════════════════
        # ═ BOTTOM PANEL: Console Logs only
        # ══════════════════════════════════════════
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(6)

        log_group = QGroupBox("📋 系統日誌")
        log_vbox = QVBoxLayout(log_group)
        self.console_edit = QTextEdit()
        self.console_edit.setReadOnly(True)
        log_vbox.addWidget(self.console_edit)
        bottom_layout.addWidget(log_group)

        # Hidden preview elements (referenced by other methods but not displayed)
        self.preview_lbl = QLabel()
        self.preview_lbl.setVisible(False)
        self.show_binarized_chk = QCheckBox()
        self.show_binarized_chk.setChecked(self.settings.get("show_binarized", False))
        self.show_binarized_chk.setVisible(False)

        splitter.addWidget(bottom_widget)

        # Set splitter proportions (tabs 75%, bottom 25%)
        splitter.setStretchFactor(0, 75)
        splitter.setStretchFactor(1, 25)

        root_layout.addWidget(splitter, 1)

        # ══════════════════════════════════════════
        # ═ POST-INIT: Populate combos
        # ══════════════════════════════════════════
        for code, name in OCREngine.get_available_languages():
            self.ocr_lang_combo.addItem(name, code)
            if code == self.settings.get("ocr_lang"):
                self.ocr_lang_combo.setCurrentIndex(self.ocr_lang_combo.count() - 1)

        self.populate_boss_combo()
        
        # Populate initial BOSS UI cards
        initial_tracker = BossTracker(self.settings.get("boss_rules", []))
        self.update_boss_ui(initial_tracker.states)
        
        # Auto-check existing Firebase connection on startup
        QTimer.singleShot(300, lambda: self.test_firebase_connection_from_ui(show_popup=False))

    def on_rule_type_changed(self, index):
        rule_type = self.rule_type_combo.currentData()
        if rule_type == "fixed":
            self.cooldown_container.setVisible(False)
            self.fixed_container.setVisible(True)
        else:
            self.cooldown_container.setVisible(True)
            self.fixed_container.setVisible(False)

    def toggle_all_day_checkboxes(self):
        all_checked = all(chk.isChecked() for chk in self.day_checkboxes)
        new_state = not all_checked
        for chk in self.day_checkboxes:
            chk.setChecked(new_state)

    def populate_boss_combo(self):
        self.correct_boss_combo.clear()
        for rule in self.settings.get("boss_rules", []):
            self.correct_boss_combo.addItem(rule["name"])

    def populate_rules_list(self):
        self.rules_list.clear()
        for rule in self.settings.get("boss_rules", []):
            rule_type = rule.get("type", "cooldown")
            tag = " [📅定時]" if rule_type == "fixed" else ""
            item = QListWidgetItem(f"{rule['name']}{tag}")
            item.setData(Qt.UserRole, rule["name"])
            self.rules_list.addItem(item)

    def load_boss_rule_details(self, item):
        boss_name = item.data(Qt.UserRole) or item.text().split(" ")[0]
        rules = self.settings.get("boss_rules", [])
        for rule in rules:
            if rule["name"] == boss_name:
                self.rule_name_edit.setText(rule["name"])
                self.rule_spawn_edit.setText(", ".join(rule.get("spawn_keywords", [])))
                self.rule_death_edit.setText(", ".join(rule.get("death_keywords", [])))
                
                rule_type = rule.get("type", "cooldown")
                idx = self.rule_type_combo.findData(rule_type)
                if idx >= 0:
                    self.rule_type_combo.setCurrentIndex(idx)
                
                if rule_type == "fixed":
                    days = rule.get("days", [0, 1, 2, 3, 4, 5, 6])
                    for chk in self.day_checkboxes:
                        day_num = chk.property("day_num")
                        chk.setChecked(day_num in days)
                    
                    fixed_times = rule.get("fixed_times", ["18:00"])
                    self.rule_fixed_times_edit.setText(", ".join(fixed_times))
                else:
                    self.rule_cooldown_spin.setValue(rule.get("cooldown_mins", 120))
                break

    def add_or_update_boss_rule(self):
        name = self.rule_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "BOSS 名稱不能為空！")
            return
            
        spawn_kws = [k.strip() for k in self.rule_spawn_edit.text().split(",") if k.strip()]
        death_kws = [k.strip() for k in self.rule_death_edit.text().split(",") if k.strip()]
        rule_type = self.rule_type_combo.currentData()
        cooldown = self.rule_cooldown_spin.value()
        
        checked_days = [chk.property("day_num") for chk in self.day_checkboxes if chk.isChecked()]
        if not checked_days:
            checked_days = [0, 1, 2, 3, 4, 5, 6] # Default to all days if none checked
            
        fixed_times_str = self.rule_fixed_times_edit.text().strip()
        fixed_times = [t.strip() for t in fixed_times_str.split(",") if t.strip()]
        if rule_type == "fixed" and not fixed_times:
            fixed_times = ["18:00"]
        
        rules = self.settings.setdefault("boss_rules", [])
        
        # Check if boss already exists
        found = False
        for rule in rules:
            if rule["name"] == name:
                rule["type"] = rule_type
                rule["spawn_keywords"] = spawn_kws
                rule["death_keywords"] = death_kws
                rule["cooldown_mins"] = cooldown
                rule["days"] = checked_days
                rule["fixed_times"] = fixed_times
                found = True
                break
                
        if not found:
            rules.append({
                "name": name,
                "type": rule_type,
                "spawn_keywords": spawn_kws,
                "death_keywords": death_kws,
                "cooldown_mins": cooldown,
                "days": checked_days,
                "fixed_times": fixed_times
            })
            
        self.populate_rules_list()
        QMessageBox.information(self, "提示", f"已在清單中新增/更新 BOSS {name} 的規則。請點擊『儲存所有 BOSS 設定』以儲存並套用！")

    def delete_boss_rule(self):
        curr_item = self.rules_list.currentItem()
        if not curr_item:
            QMessageBox.warning(self, "警告", "請先選擇清單中要刪除的 BOSS！")
            return
            
        name = curr_item.data(Qt.UserRole) or curr_item.text().split(" ")[0]
        rules = self.settings.get("boss_rules", [])
        self.settings["boss_rules"] = [r for r in rules if r["name"] != name]
        
        # Clear fields if the deleted boss is currently displayed
        if self.rule_name_edit.text() == name:
            self.rule_name_edit.clear()
            self.rule_spawn_edit.clear()
            self.rule_death_edit.clear()
            self.rule_cooldown_spin.setValue(120)
            
        self.populate_rules_list()
        
        # Purge deleted boss state from Firebase immediately if configured
        if self.worker and self.worker.firebase.is_configured():
            self.worker.firebase.delete_boss_state(name)

        QMessageBox.information(self, "提示", f"已在清單中移除 BOSS {name}。請點擊『儲存所有 BOSS 設定』以儲存並套用！")

    def save_boss_rules_to_settings(self):
        self.save_settings()
        self.populate_boss_combo()
        
        # Sync PWA firebase config
        self.write_pwa_firebase_config()
        
        rules = self.settings.get("boss_rules", [])
        
        # Hot-reload inside active worker
        if self.worker and self.worker.isRunning():
            self.worker.boss_tracker.set_rules(rules)
            # Sync states and rules to Firebase (in case rules added new ones)
            if self.worker.firebase.is_configured():
                self.worker.firebase.update_boss_states(self.worker.boss_tracker.states)
                self.worker.firebase.update_boss_rules(rules)
                self.worker.firebase.purge_stale_boss_states(rules)
            self.update_boss_ui(self.worker.boss_tracker.states)
        else:
            current_tracker = BossTracker(rules)
            self.update_boss_ui(current_tracker.states)
            fb = FirebaseClient(self.settings.get("firebase_url", ""), self.settings.get("firebase_passcode", ""))
            if fb.is_configured():
                fb.update_boss_rules(rules)
                fb.purge_stale_boss_states(rules)
            
        self.log_message("所有 BOSS 設定已成功儲存並同步！")
        QMessageBox.information(self, "提示", "BOSS 規則設定已儲存，並已即時同步套用！")

    def refresh_windows(self):
        self.win_combo.clear()
        windows = WindowCapturer.find_all_windows()
        for win in windows:
            self.win_combo.addItem(f"{win['title']} (HWND: {win['hwnd']})", win['hwnd'])
        
        if self.win_combo.count() == 0:
            self.win_combo.addItem("找不到任何天堂W視窗", None)

    def bind_window(self):
        hwnd = self.win_combo.currentData()
        if not hwnd:
            QMessageBox.warning(self, "警告", "請選擇一個有效的遊戲視窗！")
            return
        
        self.settings["hwnd"] = hwnd
        self.save_settings()
        
        # Test client rect
        capturer = WindowCapturer()
        rect = capturer.get_client_rect(hwnd)
        if rect:
            self.log_message(f"成功選定視窗 HWND: {hwnd}。視窗大小: {rect[2]-rect[0]}x{rect[3]-rect[1]}")
        else:
            self.log_message(f"選定視窗 HWND: {hwnd}，但獲取客戶區幾何失敗，請確認視窗是否已關閉。")

    def update_crop_settings(self):
        self.settings["crop_x"] = self.spin_x.value()
        self.settings["crop_y"] = self.spin_y.value()
        self.settings["crop_w"] = self.spin_w.value()
        self.settings["crop_h"] = self.spin_h.value()
        self.save_settings()
        
        if self.worker and self.worker.isRunning():
            self.worker.update_settings(self.settings)

    def update_binarized_preview_setting(self):
        self.settings["show_binarized"] = self.show_binarized_chk.isChecked()
        self.save_settings()
        if self.worker and self.worker.isRunning():
            self.worker.update_settings(self.settings)

    def save_config_from_ui(self):
        self.settings["firebase_url"] = self.fb_url_edit.text().strip()
        self.settings["firebase_passcode"] = self.fb_pass_edit.text().strip()
        self.settings["firebase_api_key"] = self.fb_api_key_edit.text().strip()
        self.settings["firebase_appcheck_token"] = self.fb_appcheck_edit.text().strip()
        self.settings["only_boss_messages"] = self.only_boss_messages_chk.isChecked()
        self.settings["use_yellow_filter"] = self.use_yellow_filter_chk.isChecked()
        self.settings["use_binarization"] = self.use_binarization_chk.isChecked()
        self.settings["ocr_threshold"] = self.ocr_threshold_spin.value()
        self.settings["ocr_interval_s"] = float(self.ocr_interval_spin.value())
        self.settings["ocr_lang"] = self.ocr_lang_combo.currentData()
        
        self.save_settings()
        self.log_message("系統設定已儲存。")
        
        # Push App Check config to Firebase so web clients sync up
        url = self.settings.get("firebase_url")
        passcode = self.settings.get("firebase_passcode")
        api_key = self.settings.get("firebase_api_key", "")
        site_key = self.settings.get("firebase_appcheck_token", "")
        if url and passcode:
            fb = FirebaseClient(url, passcode, api_key=api_key, app_check_token=site_key)
            fb.push_app_check_config(site_key)

        # Write firebase_config.json to web/data/ so GitHub Pages PWA can sync up
        self.write_pwa_firebase_config()

        # Instantly test Firebase connection with saved credentials
        self.test_firebase_connection_from_ui(show_popup=False)

        if self.worker and self.worker.isRunning():
            self.worker.update_settings(self.settings)

    def write_pwa_firebase_config(self):
        """Write configuration to web/data/firebase_config.json for frontend distribution."""
        config_path = "web/data/firebase_config.json"
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        payload = {
          "databaseURL": self.settings.get("firebase_url", ""),
          "passcode": self.settings.get("firebase_passcode", ""),
          "apiKey": self.settings.get("firebase_api_key", ""),
          "vapidPublicKey": self.settings.get("vapid_public_key", ""),
          "appCheckSiteKey": self.settings.get("firebase_appcheck_token", "")
        }
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2)
            self.log_message("已同步更新 Web 端 Firebase 配置檔。")
        except Exception as e:
            logger.error(f"Failed to write PWA config: {e}")

    def test_firebase_connection_from_ui(self, show_popup=True):
        """Instantly tests Firebase database connection with the credentials currently in UI inputs."""
        url = self.fb_url_edit.text().strip()
        passcode = self.fb_pass_edit.text().strip()
        api_key = self.fb_api_key_edit.text().strip()
        if not url:
            self.update_connection_status(False, "未設定 URL")
            if show_popup:
                QMessageBox.warning(self, "提示", "請先輸入 Firebase Database URL！\n例如：https://xxxx-default-rtdb.firebaseio.com")
            return

        client = FirebaseClient(url, passcode, api_key=api_key)
        try:
            success, msg = client.test_connection()
            self.update_connection_status(success, msg)

            if show_popup:
                if success:
                    QMessageBox.information(self, "連線成功", "🎉 已成功連線至 Firebase 資料庫！")
                else:
                    QMessageBox.critical(self, "連線失敗", f"❌ 無法連線至 Firebase 資料庫：\n{msg}\n\n請確認網址格式正確且 Firebase 資料庫規則權限已開啟。")
        finally:
            client.close()

    def start_monitoring(self):
        # Pre-save settings
        self.save_config_from_ui()

        # Start Background Worker Thread (auto-detects all windows)
        self.worker = CaptureWorker(self.settings)
        self.worker.log_signal.connect(self.log_message)
        self.worker.chat_log_signal.connect(self.log_chat_message)
        self.worker.preview_signal.connect(self.update_preview)
        self.worker.boss_states_signal.connect(self.update_boss_ui)
        self.worker.connection_status_signal.connect(self.update_connection_status)
        
        self.worker.start()

        # Update button states
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        # Trigger timer to check manual correction lists
        self.update_boss_ui(self.worker.boss_tracker.states)

    def stop_monitoring(self):
        if self.worker:
            self.worker.stop()
            self.worker = None

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        self.preview_lbl.setText("監控已停止。")
        self.fb_status_lbl.setText("● 未連線")
        self.fb_status_lbl.setStyleSheet("color: #4a5568; font-size: 12px; font-weight: bold; background: transparent;")

    def request_preview_update(self):
        pass

    def log_message(self, text):
        self.console_edit.append(text)
        # Limit console log to 300 lines to avoid RAM growth over days
        doc = self.console_edit.document()
        if doc.blockCount() > 350:
            from PySide6.QtGui import QTextCursor
            cursor = self.console_edit.textCursor()
            cursor.movePosition(QTextCursor.Start)
            for _ in range(doc.blockCount() - 300):
                cursor.select(QTextCursor.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()

    def log_chat_message(self, text, is_whitelisted=False, boss_name=""):
        # Limit UI chat list to 200 items max to prevent UI slowdown & memory leaks
        while self.chat_edit.count() >= 200:
            old_item = self.chat_edit.takeItem(0)
            if old_item:
                old_widget = self.chat_edit.itemWidget(old_item)
                if old_widget:
                    old_widget.deleteLater()
                del old_item

        # Check if user is currently at or near bottom BEFORE adding item
        vbar = self.chat_edit.verticalScrollBar()
        at_bottom = (vbar.value() >= vbar.maximum() - 40) or (self.chat_edit.count() == 0)

        item = QListWidgetItem(self.chat_edit)
        item.setSizeHint(QSize(100, 38))
        self.chat_edit.addItem(item)
        
        widget = ChatLogItemWidget(
            text, 
            is_whitelisted, 
            boss_name,
            whitelist_callback=self.toggle_whitelist_message, 
            blacklist_callback=self.exclude_message,
            edit_callback=self.correct_chat_message_by_widget, 
            parent=self
        )
        self.chat_edit.setItemWidget(item, widget)
        
        # Only auto-scroll to bottom if user was already viewing the bottom
        if at_bottom:
            self.chat_edit.scrollToBottom()

    def clear_chat_list(self):
        """Safely remove and delete all chat item widgets to free memory."""
        while self.chat_edit.count() > 0:
            old_item = self.chat_edit.takeItem(0)
            if old_item:
                old_widget = self.chat_edit.itemWidget(old_item)
                if old_widget:
                    old_widget.deleteLater()
                del old_item

    def correct_chat_message_by_widget(self, widget):
        old_cleaned = widget.content_text
        
        new_content, ok = QInputDialog.getText(
            self, 
            "手動更正對話內容", 
            "請輸入更正後的訊息內容：\n(僅針對文字，無需輸入時間)", 
            text=old_cleaned
        )
        if ok and new_content:
            new_cleaned = re.sub(r'^\[\d{2}:\d{2}(:\d{2})?\]\s*', '', new_content).strip()
            if not new_cleaned:
                return

            # Extract existing timestamp from full text
            ts_match = re.match(r'^(\[\d{2}:\d{2}(:\d{2})?\])\s*', widget.text)
            ts_str = ts_match.group(1) if ts_match else f"[{datetime.now().strftime('%H:%M:%S')}]"
            new_full = f"{ts_str} {new_cleaned}"

            # Save pure content correction mapping
            if old_cleaned != new_cleaned:
                ocr_corr = self.settings.setdefault("ocr_corrections", {})
                ocr_corr[old_cleaned] = new_cleaned
                self.save_settings()
                if self.worker:
                    self.worker.update_settings(self.settings)

            # Update widget UI
            widget.text = new_full
            widget.content_text = new_cleaned
            widget.label.setText(new_cleaned)
            
            # Evaluate boss tracker on corrected text using existing message timestamp
            parsed_line, event_time = self.parse_line_timestamp(new_full)
            tracker = self.worker.boss_tracker if (self.worker and hasattr(self.worker, "boss_tracker")) else BossTracker(self.settings.get("boss_rules", []))
            fb = self.worker.firebase if (self.worker and hasattr(self.worker, "firebase")) else FirebaseClient(self.settings.get("firebase_url"), self.settings.get("firebase_passcode"), api_key=self.settings.get("firebase_api_key"))

            matched_boss = tracker.get_matched_boss_name(new_cleaned)
            is_whitelisted = (new_cleaned in self.settings.get("whitelisted_messages", [])) or (matched_boss is not None)
            widget.set_whitelisted(is_whitelisted, matched_boss)

            events = tracker.process_ocr_lines([new_cleaned], event_time)
            if events:
                if fb.is_configured():
                    fb.update_boss_states(tracker.states)
                self.update_boss_ui(tracker.states)
                self.log_message(f"手動更正觸發 BOSS 計時更新: {new_full}")

    def correct_chat_message(self, item):
        widget = self.chat_edit.itemWidget(item)
        if widget:
            self.correct_chat_message_by_widget(widget)

    def toggle_whitelist_message(self, full_text, widget):
        cleaned_text = re.sub(r'^\[\d{2}:\d{2}(:\d{2})?\]\s*', '', full_text)
        whitelisted = self.settings.setdefault("whitelisted_messages", [])
        
        if cleaned_text not in whitelisted:
            whitelisted.append(cleaned_text)
            self.save_settings()
            self.log_message(f"已將訊息加入 BOSS 白名單：{cleaned_text}")
        else:
            self.settings["whitelisted_messages"] = [w for w in whitelisted if w != cleaned_text]
            self.save_settings()
            self.log_message(f"已從 BOSS 白名單移除訊息：{cleaned_text}")
            
        tracker = self.worker.boss_tracker if (self.worker and hasattr(self.worker, "boss_tracker")) else BossTracker(self.settings.get("boss_rules", []))
        matched_boss = tracker.get_matched_boss_name(cleaned_text)
        new_is_whitelisted = (cleaned_text in self.settings.get("whitelisted_messages", [])) or (matched_boss is not None)
                
        widget.set_whitelisted(new_is_whitelisted, matched_boss)
        
        # Trigger boss tracker if newly whitelisted
        if new_is_whitelisted:
            parsed_line, event_time = self.parse_line_timestamp(full_text)
            events = tracker.process_ocr_lines([parsed_line], event_time)
            if events:
                if self.worker and self.worker.firebase.is_configured():
                    self.worker.firebase.update_boss_states(tracker.states)
                self.update_boss_ui(tracker.states)
                self.log_message(f"白名單訊息觸發 BOSS 計時更新: {parsed_line}")

    def exclude_message(self, full_text):
        cleaned_text = re.sub(r'^\[\d{2}:\d{2}(:\d{2})?\]\s*', '', full_text)
        
        exclusions = self.settings.setdefault("excluded_messages", [])
        if cleaned_text not in exclusions:
            exclusions.append(cleaned_text)
            self.save_settings()
            self.log_message(f"已將訊息永久排除：{cleaned_text}")
            
            if self.worker:
                self.worker.update_settings(self.settings)
                
        # Remove ALL matching messages from UI list and delete widget memory
        exclusions = self.settings.get("excluded_messages", [])
        for i in range(self.chat_edit.count() - 1, -1, -1):
            item = self.chat_edit.item(i)
            widget = self.chat_edit.itemWidget(item)
            if widget:
                item_cleaned = re.sub(r'^\[\d{2}:\d{2}(:\d{2})?\]\s*', '', widget.label.text())
                if CaptureWorker.is_blacklisted_line(item_cleaned, exclusions):
                    old_item = self.chat_edit.takeItem(i)
                    if widget:
                        widget.deleteLater()
                    del old_item

    def update_preview(self, frame):
        """Converts OpenCV BGR image to QPixmap and fits it on preview label."""
        if frame is None:
            return
        
        # Convert BGR to RGB
        rgb_image = cv2_rgb = frame
        if len(frame.shape) == 3: # color image
            rgb_image = cv2_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        else: # grayscale
            h, w = frame.shape
            q_img = QImage(frame.data, w, h, w, QImage.Format_Indexed8)

        pixmap = QPixmap.fromImage(q_img)
        # Scaled to label size
        scaled_pixmap = pixmap.scaled(self.preview_lbl.width(), self.preview_lbl.height(), 
                                      Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview_lbl.setPixmap(scaled_pixmap)

    def update_boss_ui(self, states):
        """Renders clean visual card widgets for each BOSS inside self.boss_cards_layout."""
        # Clear existing widgets from grid layout
        while self.boss_cards_layout.count():
            item = self.boss_cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        if not states:
            empty_lbl = QLabel("尚未設定任何 BOSS 規則")
            empty_lbl.setAlignment(Qt.AlignCenter)
            empty_lbl.setStyleSheet("color: #4a5568; font-size: 13px; padding: 20px 0;")
            self.boss_cards_layout.addWidget(empty_lbl, 0, 0, 1, 2)
            return

        row, col = 0, 0
        max_cols = 2  # 2 cards per row

        for boss_name, state in states.items():
            status = state.get("status", "unknown")
            
            # Build Card Widget
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #141a24;
                    border: 1px solid #1e2838;
                    border-radius: 10px;
                }
                QFrame:hover {
                    border-color: #2a3d5c;
                }
            """)
            
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(6)
            card_layout.setContentsMargins(12, 10, 12, 10)

            # Header row: Boss Name + Badge
            head_row = QHBoxLayout()
            name_lbl = QLabel(f"👾 {boss_name}")
            name_lbl.setStyleSheet("color: #e2e8f0; font-size: 15px; font-weight: bold; background: transparent;")
            head_row.addWidget(name_lbl)
            head_row.addStretch()

            badge_lbl = QLabel()
            if status == "alive":
                badge_lbl.setText("● 存活中")
                badge_lbl.setStyleSheet("color: #22c55e; font-weight: bold; background: #14532d; border-radius: 6px; padding: 3px 8px; font-size: 11px;")
            elif status == "dead":
                badge_lbl.setText("● 倒數中")
                badge_lbl.setStyleSheet("color: #ef4444; font-weight: bold; background: #7f1d1d; border-radius: 6px; padding: 3px 8px; font-size: 11px;")
            else:
                badge_lbl.setText("● 未知")
                badge_lbl.setStyleSheet("color: #94a3b8; font-weight: bold; background: #1e293b; border-radius: 6px; padding: 3px 8px; font-size: 11px;")
            head_row.addWidget(badge_lbl)
            card_layout.addLayout(head_row)

            # Separator
            card_sep = QFrame()
            card_sep.setFrameShape(QFrame.HLine)
            card_sep.setStyleSheet("background-color: #1e2838; max-height: 1px;")
            card_layout.addWidget(card_sep)

            # Body info
            next_spawn = state.get("next_spawn_time", "")
            if next_spawn:
                try:
                    dt = datetime.fromisoformat(next_spawn)
                    next_spawn_str = dt.strftime("%H:%M")
                except:
                    next_spawn_str = next_spawn
            else:
                next_spawn_str = "--:--"

            info_lbl = QLabel(f"⏰ 下次重生: <b style='color: #7eb6ff; font-size: 14px;'>{next_spawn_str}</b>")
            info_lbl.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent;")
            card_layout.addWidget(info_lbl)

            reporter = state.get("reported_by", "system")
            src_lbl = QLabel(f"📌 來源: {reporter}")
            src_lbl.setStyleSheet("font-size: 11px; color: #4a5568; background: transparent;")
            card_layout.addWidget(src_lbl)

            self.boss_cards_layout.addWidget(card, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def update_connection_status(self, success, message):
        if success:
            self.fb_status_lbl.setText("● 已連線")
            self.fb_status_lbl.setStyleSheet("color: #22c55e; font-size: 12px; font-weight: bold; background: transparent;")
        else:
            self.fb_status_lbl.setText(f"● 失敗 ({message})")
            self.fb_status_lbl.setStyleSheet("color: #ef4444; font-size: 12px; font-weight: bold; background: transparent;")

    def force_boss_alive(self):
        """Force the selected boss to Alive state."""
        boss_name = self.correct_boss_combo.currentText()
        if not boss_name:
            return
        
        is_disposable_fb = False
        if self.worker and self.worker.isRunning():
            tracker = self.worker.boss_tracker
            fb = self.worker.firebase
        else:
            tracker = BossTracker(self.settings.get("boss_rules", []))
            fb = FirebaseClient(self.settings.get("firebase_url"), self.settings.get("firebase_passcode"), api_key=self.settings.get("firebase_api_key"))
            is_disposable_fb = True

        try:
            tracker.record_spawn(boss_name, now, source="manual", reporter="Host (GUI)")
            
            if fb.is_configured():
                fb.update_boss_states(tracker.states)

            self.update_boss_ui(tracker.states)
            self.log_message(f"主控端手動強制 BOSS {boss_name} 為『存活中』")
        finally:
            if is_disposable_fb:
                fb.close()

    def force_boss_dead(self):
        """Force the selected boss to Dead state."""
        boss_name = self.correct_boss_combo.currentText()
        if not boss_name:
            return
        
        now = datetime.now()
        death_time = now
        
        if self.use_custom_death_time_chk.isChecked():
            qtime = self.custom_death_time.time()
            death_time = now.replace(hour=qtime.hour(), minute=qtime.minute(), second=0, microsecond=0)
            from datetime import timedelta
            if death_time > now:
                death_time -= timedelta(days=1)
        
        is_disposable_fb = False
        if self.worker and self.worker.isRunning():
            tracker = self.worker.boss_tracker
            fb = self.worker.firebase
        else:
            tracker = BossTracker(self.settings.get("boss_rules", []))
            fb = FirebaseClient(self.settings.get("firebase_url"), self.settings.get("firebase_passcode"), api_key=self.settings.get("firebase_api_key"))
            is_disposable_fb = True

        try:
            tracker.record_death(boss_name, death_time, source="manual", reporter="Host (GUI)")
            
            if fb.is_configured():
                fb.update_boss_states(tracker.states)

            self.update_boss_ui(tracker.states)
            
            death_time_str = death_time.strftime("%H:%M")
            self.log_message(f"主控端手動強制 BOSS {boss_name} 為『已死亡』(死亡時間: {death_time_str})，計時重置！")
        finally:
            if is_disposable_fb:
                fb.close()

    def test_single_ocr(self):
        """Captures a single frame, runs OCR, and displays the raw results in a popup to help with troubleshooting."""
        # Auto-detect first available game window
        windows = WindowCapturer.find_all_windows()
        if not windows:
            QMessageBox.warning(self, "警告", "找不到任何天堂W遊戲視窗！請確認遊戲是否已啟動。")
            return
        hwnd = windows[0]['hwnd']
        if not win32gui.IsWindow(hwnd):
            QMessageBox.warning(self, "警告", "偵測到的遊戲視窗已失效，請確認遊戲視窗狀態。")
            return
            
        # Get coordinates
        rx = self.spin_x.value()
        ry = self.spin_y.value()
        rw = self.spin_w.value()
        rh = self.spin_h.value()
        region = (rx, ry, rw, rh)
        
        self.log_message("正在執行測試單次辨識...")
        
        # Capture
        capturer = WindowCapturer()
        frame = capturer.capture_client_area(hwnd, region)
        capturer.close()
        
        if frame is None:
            QMessageBox.critical(self, "錯誤", "擷圖失敗！請確認遊戲視窗未最小化或未關閉。")
            return
            
        # Run OCR
        threshold_val = self.ocr_threshold_spin.value()
        ocr_engine = OCREngine(lang=self.ocr_lang_combo.currentData())
        ocr_res = ocr_engine.recognize_text(
            frame, 
            threshold_val=threshold_val, 
            scale=2, 
            use_binarization=self.settings.get("use_binarization", False),
            use_yellow_filter=self.settings.get("use_yellow_filter", True)
        )
        
        raw_text = ocr_res.get("text", "").strip()
        lines = ocr_res.get("lines", [])
        
        # Display results
        if not raw_text:
            msg = (
                "辨識結果為空！\n\n"
                "可能原因：\n"
                "1. 擷取範圍未對準聊天室（請確認『對話擷取區域預覽』中是否包含文字）。\n"
                "2. 二值化閥值太高或太低（請勾選『顯示二值化黑白影像』，若畫面全黑請調低閥值，若全白請調高閥值）。"
            )
            QMessageBox.warning(self, "測試辨識結果", msg)
        else:
            lines_str = "\n".join([f"- {line}" for line in lines])
            msg = (
                f"辨識成功！共偵測到 {len(lines)} 行文字：\n\n"
                f"{lines_str}\n\n"
                f"完整辨識內容：\n{raw_text}"
            )
            QMessageBox.information(self, "測試辨識結果", msg)

    def closeEvent(self, event):
        # Stop worker when closing UI
        if self.worker:
            self.worker.stop()
        event.accept()
