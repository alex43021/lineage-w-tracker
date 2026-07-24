import difflib
import logging

logger = logging.getLogger(__name__)

class ChatDeduplicator:
    def __init__(self, max_history=150, threshold=0.78):
        """
        max_history: Max number of unique lines to store in the historical buffer.
        threshold: SequenceMatcher similarity ratio [0.0 - 1.0]. Lines above this ratio
                   are treated as duplicates of already seen messages.
        """
        self.history = []
        self.max_history = max_history
        self.threshold = threshold

    def add_lines(self, new_lines):
        """
        Compare each incoming OCR line against recent history.
        Resilient against message deletions, edits, and un-sent messages.
        Only returns truly new or modified lines.
        """
        cleaned_new = [line.strip() for line in new_lines if line.strip()]
        if not cleaned_new:
            return []

        truly_new_lines = []

        for line in cleaned_new:
            is_seen = False
            # Check against the last 30 lines in self.history
            recent_history = self.history[-30:] if len(self.history) > 30 else self.history
            
            for hist_line in reversed(recent_history):
                # 1. Exact string match check
                if line == hist_line:
                    is_seen = True
                    break

                # 2. SequenceMatcher fuzzy similarity check
                ratio = difflib.SequenceMatcher(None, hist_line, line).ratio()
                if ratio >= self.threshold:
                    is_seen = True
                    logger.debug(f"Filtered out duplicate message: '{line}' matches '{hist_line}' ({ratio:.2f})")
                    break

            if not is_seen:
                truly_new_lines.append(line)
                self.history.append(line)

        # Enforce history size limit
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        return truly_new_lines

    def clear(self):
        """Clear the history buffer."""
        self.history = []
