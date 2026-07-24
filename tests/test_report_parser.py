import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from datetime import datetime, timedelta
from core.boss_tracker import BossTracker

class TestBossTracker(unittest.TestCase):
    def setUp(self):
        self.rules = [
            {
                "name": "巴風特",
                "spawn_keywords": ["巴風特", "出現"],
                "death_keywords": ["巴風特", "擊敗"],
                "cooldown_mins": 120
            }
        ]
        self.tracker = BossTracker(self.rules)

    def test_ocr_detection(self):
        lines = ["[系統] 奇岩地監的巴風特已出現了。"]
        now = datetime.now()
        events = self.tracker.process_ocr_lines(lines, now)
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["boss"], "巴風特")
        self.assertEqual(events[0]["type"], "spawn")
        self.assertEqual(self.tracker.states["巴風特"]["status"], "alive")

        lines_death = ["恭喜玩家A擊敗了巴風特。"]
        events_death = self.tracker.process_ocr_lines(lines_death, now)
        self.assertEqual(len(events_death), 1)
        self.assertEqual(events_death[0]["type"], "death")
        self.assertEqual(self.tracker.states["巴風特"]["status"], "dead")
        
        # Next spawn should be +120 mins
        expected_spawn = now + timedelta(minutes=120)
        self.assertEqual(self.tracker.states["巴風特"]["next_spawn_time"], expected_spawn.isoformat())

    def test_manual_report_now(self):
        report = {
            "boss_name": "巴風特",
            "time_type": "now",
            "reported_by": "小明",
            "passcode": "7777",
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
        event = self.tracker.process_manual_report(report)
        self.assertIsNotNone(event)
        self.assertEqual(event["type"], "death")
        self.assertEqual(self.tracker.states["巴風特"]["status"], "dead")
        self.assertEqual(self.tracker.states["巴風特"]["source"], "manual")

    def test_manual_report_custom_time(self):
        now = datetime.now()
        # Report that it died at 12:34
        report = {
            "boss_name": "巴風特",
            "time_type": "custom",
            "custom_time": "12:34",
            "reported_by": "小明",
            "passcode": "7777",
            "timestamp": int(now.timestamp() * 1000)
        }
        event = self.tracker.process_manual_report(report)
        self.assertIsNotNone(event)
        
        death_time_str = self.tracker.states["巴風特"]["last_death_time"]
        death_time = datetime.fromisoformat(death_time_str)
        
        self.assertEqual(death_time.hour, 12)
        self.assertEqual(death_time.minute, 34)

    def test_conflict_resolution_ocr_overrides_manual(self):
        now = datetime.now()
        
        # 1. First, a manual report at 12:00
        manual_time = now.replace(hour=12, minute=0, second=0, microsecond=0)
        self.tracker.record_death("巴風特", manual_time, source="manual", reporter="小明")
        self.assertEqual(self.tracker.states["巴風特"]["source"], "manual")
        self.assertEqual(self.tracker.states["巴風特"]["last_death_time"], manual_time.isoformat())

        # 2. Then, OCR detects death at 12:05 (different time, but same cycle)
        ocr_time = now.replace(hour=12, minute=5, second=0, microsecond=0)
        self.tracker.record_death("巴風特", ocr_time, source="ocr", reporter="OCR")
        
        # OCR should override the manual time!
        self.assertEqual(self.tracker.states["巴風特"]["source"], "ocr")
        self.assertEqual(self.tracker.states["巴風特"]["last_death_time"], ocr_time.isoformat())

    def test_conflict_resolution_discard_manual_if_ocr_exists(self):
        now = datetime.now()
        
        # 1. OCR detects death at 12:00
        ocr_time = now.replace(hour=12, minute=0, second=0, microsecond=0)
        self.tracker.record_death("巴風特", ocr_time, source="ocr", reporter="OCR")
        self.assertEqual(self.tracker.states["巴風特"]["source"], "ocr")

        # 2. Later, a manual report is submitted for 12:05 (same cycle)
        manual_time = now.replace(hour=12, minute=5, second=0, microsecond=0)
        event = self.tracker.record_death("巴風特", manual_time, source="manual", reporter="小明")
        
        # The manual report should be discarded!
        self.assertIsNone(event)
        self.assertEqual(self.tracker.states["巴風特"]["source"], "ocr")
        self.assertEqual(self.tracker.states["巴風特"]["last_death_time"], ocr_time.isoformat())

if __name__ == '__main__':
    unittest.main()
