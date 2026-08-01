import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from core.boss_tracker import BossTracker

class TestFixedSchedule(unittest.TestCase):
    def test_daily_fixed_spawn(self):
        # Current time: Saturday 2026-08-01 15:00
        ref_dt = datetime(2026, 8, 1, 15, 0, 0)
        
        # Rule: Daily at 18:00
        days = [0, 1, 2, 3, 4, 5, 6] # Sun - Sat
        fixed_times = ["18:00"]
        
        next_iso = BossTracker.calculate_next_fixed_spawn(days, fixed_times, ref_dt)
        self.assertIsNotNone(next_iso)
        # Should be today 18:00
        expected_iso = datetime(2026, 8, 1, 18, 0, 0).isoformat()
        self.assertEqual(next_iso, expected_iso)

    def test_daily_fixed_spawn_past_time(self):
        # Current time: Saturday 2026-08-01 20:00 (past 18:00)
        ref_dt = datetime(2026, 8, 1, 20, 0, 0)
        
        days = [0, 1, 2, 3, 4, 5, 6]
        fixed_times = ["18:00"]
        
        next_iso = BossTracker.calculate_next_fixed_spawn(days, fixed_times, ref_dt)
        self.assertIsNotNone(next_iso)
        # Should be tomorrow (Sunday 2026-08-02) 18:00
        expected_iso = datetime(2026, 8, 2, 18, 0, 0).isoformat()
        self.assertEqual(next_iso, expected_iso)

    def test_weekly_fixed_spawn(self):
        # Current time: Saturday 2026-08-01 10:00 (Saturday is JS day 6, Py weekday 5)
        ref_dt = datetime(2026, 8, 1, 10, 0, 0)
        
        # Rule: Every Wednesday (JS day 3) at 19:00
        days = [3] # Wednesday
        fixed_times = ["19:00"]
        
        next_iso = BossTracker.calculate_next_fixed_spawn(days, fixed_times, ref_dt)
        self.assertIsNotNone(next_iso)
        # Wednesday is 2026-08-05
        expected_iso = datetime(2026, 8, 5, 19, 0, 0).isoformat()
        self.assertEqual(next_iso, expected_iso)

if __name__ == '__main__':
    unittest.main()
