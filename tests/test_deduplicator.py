import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from core.chat_deduplicator import ChatDeduplicator

class TestChatDeduplicator(unittest.TestCase):
    def setUp(self):
        # Default dedup threshold of 75%
        self.dedup = ChatDeduplicator(max_history=10, threshold=0.75)

    def test_empty_initial(self):
        new_lines = ["[12:00] PlayerA: Hello", "[12:01] PlayerB: How are you"]
        added = self.dedup.add_lines(new_lines)
        self.assertEqual(added, ["[12:00] PlayerA: Hello", "[12:01] PlayerB: How are you"])
        self.assertEqual(self.dedup.history, ["[12:00] PlayerA: Hello", "[12:01] PlayerB: How are you"])

    def test_perfect_scroll_overlap(self):
        # Initial
        self.dedup.add_lines(["[12:00] PlayerA: Hello", "[12:01] PlayerB: How are you", "[12:02] PlayerC: Let's go to dungeon"])
        
        # Scrolled
        incoming = ["[12:01] PlayerB: How are you", "[12:02] PlayerC: Let's go to dungeon", "[12:03] PlayerD: Count me in"]
        added = self.dedup.add_lines(incoming)
        
        self.assertEqual(added, ["[12:03] PlayerD: Count me in"])
        self.assertEqual(self.dedup.history, [
            "[12:00] PlayerA: Hello",
            "[12:01] PlayerB: How are you",
            "[12:02] PlayerC: Let's go to dungeon",
            "[12:03] PlayerD: Count me in"
        ])

    def test_fuzzy_scroll_overlap(self):
        # Initial
        self.dedup.add_lines(["[12:00] PlayerA: 哈囉大家", "[12:01] PlayerB: 買防卷"])
        
        # Scrolled, but with OCR error on PlayerB (e.g. 買 -> 賣, 卷 -> 券)
        incoming = ["[12:01] PlayerB: 賣防券", "[12:02] PlayerC: 盟戰開始了"]
        added = self.dedup.add_lines(incoming)
        
        # Overlap of size 1 (PlayerB) should be recognized due to high similarity
        self.assertEqual(added, ["[12:02] PlayerC: 盟戰開始了"])

    def test_no_overlap(self):
        self.dedup.add_lines(["[12:00] PlayerA: Hello", "[12:01] PlayerB: How are you"])
        incoming = ["[12:10] System: Boss Baphomet has spawned", "[12:11] PlayerE: Go go go"]
        added = self.dedup.add_lines(incoming)
        
        # No overlap, all should be added
        self.assertEqual(added, ["[12:10] System: Boss Baphomet has spawned", "[12:11] PlayerE: Go go go"])

    def test_empty_input(self):
        self.dedup.add_lines(["Line A"])
        added = self.dedup.add_lines(["", "   "])
        self.assertEqual(added, [])

if __name__ == '__main__':
    unittest.main()
