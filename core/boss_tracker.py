import logging
from datetime import datetime, timedelta
import re
import difflib

logger = logging.getLogger(__name__)

class BossTracker:
    def __init__(self, rules=None):
        """
        rules: List of dicts representing boss configurations:
               [
                 {
                   "name": "巴風特",
                   "spawn_keywords": ["巴風特", "出現"],
                   "death_keywords": ["巴風特", "擊敗"],
                   "cooldown_mins": 120
                 }
               ]
        """
        self.rules = rules if rules else []
        self.states = {}
        self.initialize_states()

    @staticmethod
    def calculate_next_fixed_spawn(days=None, fixed_times=None, reference_dt=None):
        """
        Calculate the next upcoming ISO datetime string for a fixed schedule boss.
        days: List of integers (0=Sun, 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri, 6=Sat).
              If empty or None, defaults to all days [0, 1, 2, 3, 4, 5, 6] (Daily).
        fixed_times: List of HH:MM strings e.g. ["18:00", "22:00"].
        """
        if not reference_dt:
            reference_dt = datetime.now()
        if not fixed_times:
            return None
            
        valid_days = days if (days is not None and len(days) > 0) else [0, 1, 2, 3, 4, 5, 6]
        
        # Python datetime.weekday(): Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
        # Convert JS/Standard 0=Sun to Python weekday:
        py_valid_days = set([(int(d) - 1) % 7 for d in valid_days])

        min_candidate = None

        for day_offset in range(8):
            candidate_date = (reference_dt + timedelta(days=day_offset)).date()
            if candidate_date.weekday() not in py_valid_days:
                continue

            for time_str in fixed_times:
                try:
                    parts = str(time_str).strip().split(':')
                    if len(parts) < 2:
                        continue
                    hh, mm = int(parts[0]), int(parts[1])
                    candidate_dt = datetime.combine(candidate_date, datetime.min.time()).replace(hour=hh, minute=mm)
                    
                    if candidate_dt > reference_dt:
                        if min_candidate is None or candidate_dt < min_candidate:
                            min_candidate = candidate_dt
                except Exception:
                    pass

        return min_candidate.isoformat() if min_candidate else None

    def initialize_states(self):
        """Initialize state dictionary for all bosses."""
        for rule in self.rules:
            name = rule["name"]
            rule_type = rule.get("type", "cooldown")
            days = rule.get("days", [0, 1, 2, 3, 4, 5, 6])
            fixed_times = rule.get("fixed_times", ["18:00"])
            cooldown_mins = rule.get("cooldown_mins", 60)

            next_fixed = None
            if rule_type == "fixed":
                next_fixed = self.calculate_next_fixed_spawn(days, fixed_times, datetime.now())

            self.states[name] = {
                "name": name,
                "type": rule_type,
                "status": "unknown",          # "unknown", "alive", "dead"
                "last_spawn_time": None,      # ISO timestamp
                "last_death_time": None,      # ISO timestamp
                "next_spawn_time": next_fixed, # ISO timestamp
                "source": "none",             # "none", "ocr", "manual", "fixed_schedule"
                "reported_by": "system",
                "days": days,
                "fixed_times": fixed_times,
                "cooldown_mins": cooldown_mins
            }

    def set_rules(self, rules):
        self.rules = rules
        new_states = {}
        for rule in self.rules:
            name = rule["name"]
            rule_type = rule.get("type", "cooldown")
            days = rule.get("days", [0, 1, 2, 3, 4, 5, 6])
            fixed_times = rule.get("fixed_times", ["18:00"])
            cooldown_mins = rule.get("cooldown_mins", 60)

            if name in self.states:
                st = self.states[name]
                st["type"] = rule_type
                st["cooldown_mins"] = cooldown_mins
                st["days"] = days
                st["fixed_times"] = fixed_times
                
                if rule_type == "fixed":
                    st["next_spawn_time"] = self.calculate_next_fixed_spawn(days, fixed_times, datetime.now())
                elif st.get("last_death_time"):
                    try:
                        death_dt = datetime.fromisoformat(st["last_death_time"])
                        next_dt = death_dt + timedelta(minutes=cooldown_mins)
                        st["next_spawn_time"] = next_dt.isoformat()
                    except Exception as e:
                        logger.error(f"Failed to recalculate next_spawn_time for {name}: {e}")
                new_states[name] = st
            else:
                next_fixed = None
                if rule_type == "fixed":
                    next_fixed = self.calculate_next_fixed_spawn(days, fixed_times, datetime.now())
                new_states[name] = {
                    "name": name,
                    "type": rule_type,
                    "status": "unknown",
                    "last_spawn_time": None,
                    "last_death_time": None,
                    "next_spawn_time": next_fixed,
                    "source": "none",
                    "reported_by": "system",
                    "days": days,
                    "fixed_times": fixed_times,
                    "cooldown_mins": cooldown_mins
                }
        self.states = new_states

    def update_states_from_db(self, db_states):
        """
        Merge remote boss states from Firebase DB into local tracker states.
        """
        if not db_states or not isinstance(db_states, dict):
            return False
        import urllib.parse
        updated = False
        for raw_name, db_st in db_states.items():
            name = urllib.parse.unquote(raw_name)
            if name in self.states and isinstance(db_st, dict):
                if db_st.get("last_spawn_time") or db_st.get("last_death_time") or db_st.get("next_spawn_time"):
                    self.states[name].update(db_st)
                    self.states[name]["name"] = name
                    updated = True
        return updated

    def process_ocr_lines(self, lines, timestamp=None):
        """
        Process newly captured OCR lines to detect boss spawn or death.
        lines: List of strings.
        timestamp: datetime of the capture. Defaults to now.
        Returns: List of events detected: [{"boss": ..., "type": "spawn"|"death", "time": ...}]
        """
        if not timestamp:
            timestamp = datetime.now()

        events_detected = []

        for line in lines:
            for rule in self.rules:
                boss_name = rule["name"]
                
                # Check spawn keywords
                spawn_match = self._check_keywords(line, rule.get("spawn_keywords", []))
                # Check death keywords
                death_match = self._check_keywords(line, rule.get("death_keywords", []))

                if spawn_match:
                    event = self.record_spawn(boss_name, timestamp, source="ocr", reporter="OCR")
                    if event:
                        events_detected.append(event)
                elif death_match:
                    event = self.record_death(boss_name, timestamp, source="ocr", reporter="OCR")
                    if event:
                        events_detected.append(event)

        return events_detected

    def _check_keywords(self, line, keywords):
        """
        Check if keywords match the line.
        Supports fuzzy matching and common synonym variations for robust OCR.
        """
        if not keywords:
            return False
            
        line_lower = line.lower()
        
        # 1. Exact or fuzzy match for all keywords
        all_matched = True
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in line_lower:
                continue
            # Try fuzzy check if length of keyword is at least 3 characters
            found_fuzzy = False
            if len(kw_lower) >= 3:
                for i in range(len(line_lower) - len(kw_lower) + 1):
                    sub = line_lower[i:i+len(kw_lower)]
                    sim = difflib.SequenceMatcher(None, sub, kw_lower).ratio()
                    if sim >= 0.75: # 75% character similarity
                        found_fuzzy = True
                        break
            if not found_fuzzy:
                all_matched = False
                break
                
        if all_matched:
            return True

        # 2. Resilient Fallback: If the primary Boss Name keyword is in line, check for generic action indicators
        if len(keywords) >= 2:
            boss_name_kw = keywords[0].lower()
            if boss_name_kw in line_lower:
                action_kw = keywords[1].lower()
                # If secondary keyword is a death term ("擊敗", "死亡", etc.)
                if any(term in action_kw for term in ["擊", "敗", "死", "消"]):
                    if any(term in line_lower for term in ["擊", "敗", "死", "消", "倒", "陣"]):
                        return True
                # If secondary keyword is a spawn term ("出現", "重生", etc.)
                if any(term in action_kw for term in ["現", "生", "臨", "出"]):
                    if any(term in line_lower for term in ["現", "生", "臨", "出", "降", "到"]):
                        return True
                        
        return False

    def contains_any_boss_name(self, line):
        """
        Check if line contains any configured boss name (protects boss lines from blacklists).
        """
        if not line:
            return False
        line_lower = line.lower()
        for rule in self.rules:
            boss_name = rule.get("name", "")
            if boss_name and boss_name.lower() in line_lower:
                return True
        return False

    def is_boss_related_line(self, line):
        """
        Check if a given line matches spawn or death keywords of ANY configured BOSS rule (Whitelist check).
        """
        return self.get_matched_boss_name(line) is not None or self.contains_any_boss_name(line)

    def get_matched_boss_name(self, line):
        """
        Returns the boss name if the line matches spawn or death keywords of a configured rule, else None.
        """
        if not line:
            return None
        for rule in self.rules:
            if self._check_keywords(line, rule.get("spawn_keywords", [])) or \
               self._check_keywords(line, rule.get("death_keywords", [])):
                return rule["name"]
        return None

    def record_spawn(self, boss_name, time_obj, source="ocr", reporter="system"):
        """Record boss spawn event."""
        if boss_name not in self.states:
            return None

        state = self.states[boss_name]
        time_str = time_obj.isoformat()

        # Rule: OCR takes absolute precedence over manual
        if source == "manual" and state["source"] == "ocr":
            # If there is already an active OCR spawn/status in the same cycle, discard manual
            if state["status"] == "alive":
                logger.info(f"Discarding manual spawn report for {boss_name} because active OCR status is 'alive'")
                return None

        # Update state
        state["status"] = "alive"
        state["last_spawn_time"] = time_str
        state["next_spawn_time"] = None  # Already spawned, reset next time
        state["source"] = source
        state["reported_by"] = reporter

        logger.info(f"Recorded spawn for {boss_name} at {time_str} via {source} ({reporter})")
        return {"boss": boss_name, "type": "spawn", "time": time_str, "source": source}

    @staticmethod
    def _parse_datetime(iso_str):
        """Parse ISO string cleanly, converting UTC/tz-aware strings to local naive datetime."""
        if not iso_str:
            return None
        try:
            clean_str = str(iso_str).replace('Z', '+00:00')
            dt = datetime.fromisoformat(clean_str)
            if dt.tzinfo is not None:
                dt = dt.astimezone().replace(tzinfo=None)
            return dt
        except Exception:
            return None

    def record_death(self, boss_name, time_obj, source="ocr", reporter="system"):
        """
        Record boss death event.
        Includes conflict resolution: If OCR-detected time conflicts with manual, OCR overrides.
        """
        if boss_name not in self.states:
            return None

        state = self.states[boss_name]
        time_str = time_obj.isoformat()

        if state.get("type") == "fixed":
            next_spawn_str = self.calculate_next_fixed_spawn(
                state.get("days", [0, 1, 2, 3, 4, 5, 6]),
                state.get("fixed_times", ["18:00"]),
                time_obj
            )
            next_spawn_time = datetime.fromisoformat(next_spawn_str) if next_spawn_str else time_obj
        else:
            cooldown_delta = timedelta(minutes=state["cooldown_mins"])
            next_spawn_time = time_obj + cooldown_delta
            next_spawn_str = next_spawn_time.isoformat()

        # Conflict resolution logic
        if state.get("last_death_time"):
            last_death = self._parse_datetime(state["last_death_time"])
            if last_death:
                time_diff_mins = abs((time_obj - last_death).total_seconds()) / 60.0

                # If the events are close (within the boss cooldown window), they represent the same death event
                is_same_cycle = time_diff_mins < (state["cooldown_mins"] * 0.8)

                if is_same_cycle:
                    # Case 1: New report is manual, but existing state was OCR
                    if source == "manual" and state.get("source") == "ocr":
                        logger.info(f"Discarding manual death report for {boss_name} at {time_str} because OCR record exists.")
                        return None

                    # Case 2: New report is OCR, but existing state was manual
                    if source == "ocr" and state.get("source") == "manual":
                        logger.info(f"OCR overrides manual death report for {boss_name}. Updating death time from {state['last_death_time']} to {time_str} (OCR).")

        # Update state
        state["status"] = "dead"
        state["last_death_time"] = time_str
        state["next_spawn_time"] = next_spawn_str
        state["source"] = source
        state["reported_by"] = reporter
        state["is_overdue"] = False

        logger.info(f"Recorded death for {boss_name} at {time_str} via {source}. Next spawn: {next_spawn_str}")
        return {"boss": boss_name, "type": "death", "time": time_str, "next_spawn": next_spawn_str, "source": source}

    def check_and_roll_overdue_bosses(self, now=None):
        """
        If a boss reaches its next_spawn_time but nobody reported death or OCR didn't catch it,
        automatically roll next_spawn_time forward to the next cycle (+cooldown_mins)
        and mark is_overdue = True.
        """
        if not now:
            now = datetime.now()

        updated = False
        for name, state in self.states.items():
            if state.get("next_spawn_time"):
                spawn_dt = self._parse_datetime(state["next_spawn_time"])
                if spawn_dt and now > spawn_dt:
                    cooldown = state.get("cooldown_mins", 60)
                    cooldown_delta = timedelta(minutes=cooldown)
                    curr = spawn_dt
                    while curr <= now:
                        curr += cooldown_delta
                    state["next_spawn_time"] = curr.isoformat()
                    state["is_overdue"] = True
                    updated = True
        return updated

    def process_manual_report(self, report_data):
        """
        Process a manual death report from Firebase.
        """
        boss_name = report_data.get("boss_name")
        if boss_name not in self.states:
            return None

        reported_by = report_data.get("reported_by", "Guest")
        time_type = report_data.get("time_type", "now")
        
        now = datetime.now()
        death_time = now

        if time_type == "custom":
            custom_time_str = report_data.get("custom_time", "")
            match = re.match(r"^(\d{1,2}):(\d{2})$", custom_time_str)
            if match:
                hours, minutes = int(match.group(1)), int(match.group(2))
                death_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                if death_time > now:
                    death_time -= timedelta(days=1)
            else:
                logger.warning(f"Invalid custom time format '{custom_time_str}'. Defaulting to now.")
        elif report_data.get("timestamp"):
            ts_val = report_data.get("timestamp")
            parsed_dt = self._parse_datetime(ts_val)
            if parsed_dt:
                death_time = parsed_dt

        return self.record_death(boss_name, death_time, source="manual", reporter=reported_by)
