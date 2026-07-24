import difflib
import logging

logger = logging.getLogger(__name__)

class ChatDeduplicator:
    def __init__(self, max_history=100, threshold=0.75):
        """
        max_history: Max number of unique lines to store in the historical buffer.
        threshold: SequenceMatcher similarity ratio [0.0 - 1.0]. Slices with avg similarity
                   above this threshold are treated as duplicates.
        """
        self.history = []
        self.max_history = max_history
        self.threshold = threshold

    def add_lines(self, new_lines):
        """
        Compare the incoming list of OCR lines with historical lines to find the overlap.
        Appends only the newly scrolled lines and returns them.
        """
        # Clean lines and filter out empty/whitespace-only lines
        cleaned_new = [line.strip() for line in new_lines if line.strip()]
        if not cleaned_new:
            return []

        # If history is empty, everything is new
        if not self.history:
            self.history.extend(cleaned_new)
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]
            return cleaned_new

        best_overlap_size = 0
        max_possible_overlap = min(len(self.history), len(cleaned_new))

        # Scan for overlap from largest possible overlap size down to 1
        for k in range(max_possible_overlap, 0, -1):
            history_slice = self.history[-k:]
            new_lines_slice = cleaned_new[:k]

            total_similarity = 0.0
            for h_line, n_line in zip(history_slice, new_lines_slice):
                # Calculate similarity ratio
                ratio = difflib.SequenceMatcher(None, h_line, n_line).ratio()
                total_similarity += ratio

            avg_similarity = total_similarity / k

            # If the average similarity of the overlap is high enough, we found the alignment point
            if avg_similarity >= self.threshold:
                best_overlap_size = k
                logger.debug(f"Found chat overlap alignment of size {k} with similarity {avg_similarity:.4f}")
                break

        # The new lines are everything after the overlap alignment point
        newly_added = cleaned_new[best_overlap_size:]

        # Secondary filter: verify that each newly added line is not highly similar 
        # to any line in the recent history (e.g., last 15 lines)
        filtered_newly_added = []
        for line in newly_added:
            is_duplicate = False
            # Check against the last 15 lines in self.history
            recent_history = self.history[-15:]
            for hist_line in recent_history:
                ratio = difflib.SequenceMatcher(None, hist_line, line).ratio()
                if ratio >= self.threshold:
                    is_duplicate = True
                    logger.debug(f"Filtered out duplicate line by similarity check: '{line}' matches '{hist_line}' (ratio: {ratio:.4f})")
                    break
            if not is_duplicate:
                filtered_newly_added.append(line)
                self.history.append(line)

        # Enforce history size limit
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        return filtered_newly_added

    def clear(self):
        """Clear the history buffer."""
        self.history = []
