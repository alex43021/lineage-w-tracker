import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from ui.main_window import CaptureWorker

class TestBlacklistWildcard(unittest.TestCase):
    def test_short_length_exclusion(self):
        exclusions = []
        # Any string with length < 4 should be automatically excluded
        self.assertTrue(CaptureWorker.is_blacklisted_line("1", exclusions))
        self.assertTrue(CaptureWorker.is_blacklisted_line("CP", exclusions))
        self.assertTrue(CaptureWorker.is_blacklisted_line("3個", exclusions))
        self.assertTrue(CaptureWorker.is_blacklisted_line("  G  ", exclusions))

    def test_wildcard_matching(self):
        exclusions = [
            "*得*",
            "*卡片*",
            "*1個*",
            "*派遣*",
            "*已登入*",
            "特定廣播"
        ]
        
        # Test positive wildcard matches
        self.assertTrue(CaptureWorker.is_blacklisted_line("在望虛的裂痘第1屠雅得了", exclusions))
        self.assertTrue(CaptureWorker.is_blacklisted_line("[隊員]爆焰飽哮虎獲得了安歐林的痕跡1個。", exclusions))
        self.assertTrue(CaptureWorker.is_blacklisted_line("好友樹蛙藍教頭已登入。", exclusions))
        self.assertTrue(CaptureWorker.is_blacklisted_line("妖魔城堡守衛塔派遣中有死亡的隊員。", exclusions))
        self.assertTrue(CaptureWorker.is_blacklisted_line("玩家獲得了變身卡片一張", exclusions))
        self.assertTrue(CaptureWorker.is_blacklisted_line("這是一條特定廣播訊息", exclusions))
        
        # Test negative matches (BOSS announcements must NOT be blacklisted)
        self.assertFalse(CaptureWorker.is_blacklisted_line("巴風特在死亡廢墟出現了", exclusions))
        self.assertFalse(CaptureWorker.is_blacklisted_line("那魯加的冠軍撤退了", exclusions))
        self.assertFalse(CaptureWorker.is_blacklisted_line("卡司特的頭目逃到地洞裡去了。", exclusions))

if __name__ == '__main__':
    unittest.main()
