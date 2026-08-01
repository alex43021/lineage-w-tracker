import logging
import requests
import json

logger = logging.getLogger(__name__)

class FirebaseClient:
    def __init__(self, db_url=None, passcode=None):
        """
        db_url: Firebase Realtime Database URL, e.g. "https://my-project-default-rtdb.firebaseio.com"
        passcode: The guild password, used as a secure namespace path.
        """
        self._db_url = None
        self.db_url = db_url
        self.passcode = passcode if passcode else "default"
        
        # Persistent HTTP session for connection pooling and keep-alive
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=5, pool_maxsize=10, max_retries=2)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    @property
    def db_url(self):
        return self._db_url

    @db_url.setter
    def db_url(self, val):
        if val and isinstance(val, str) and val.strip():
            self._db_url = val.strip().rstrip("/")
        else:
            self._db_url = None

    def is_configured(self):
        return bool(self.db_url)

    def _get_url(self, path):
        if not self.db_url:
            return None
        # Namespace under lineage_w_tracker/<passcode>/<path>.json
        return f"{self.db_url}/lineage_w_tracker/{self.passcode}/{path}.json"

    def test_connection(self):
        """Test connection by writing a dummy status code."""
        url = self._get_url("status")
        if not url:
            return False, "Database URL is not configured."
        try:
            response = self.session.put(url, json={"online": True, "last_ping": "now"}, timeout=5)
            if response.status_code == 200:
                return True, "Connection successful."
            return False, f"Server returned status code {response.status_code}: {response.text}"
        except Exception as e:
            return False, f"Request failed: {e}"

    def get_boss_states(self):
        """
        Fetch existing boss states from Firebase DB.
        Returns a dict of boss states or empty dict.
        """
        url = self._get_url("boss_states")
        if not url:
            return {}
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data if isinstance(data, dict) else {}
            return {}
        except Exception as e:
            logger.error(f"Firebase get_boss_states failed: {e}")
            return {}

    def update_boss_states(self, states):
        """Upload current boss states using non-destructive safe merge."""
        url = self._get_url("boss_states")
        if not url or not isinstance(states, dict):
            return False
        try:
            # First fetch current remote states to preserve existing active timestamps
            existing = self.get_boss_states()
            merged = {}
            if existing and isinstance(existing, dict):
                import urllib.parse
                for k, v in existing.items():
                    raw_k = urllib.parse.unquote(k)
                    if isinstance(v, dict):
                        merged[raw_k] = v

            for k, v in states.items():
                if isinstance(v, dict):
                    if k not in merged:
                        merged[k] = v
                    else:
                        # Only overwrite timestamps if new state actually has a timestamp
                        if v.get("next_spawn_time") or v.get("last_death_time") or v.get("last_spawn_time"):
                            merged[k].update(v)
                        else:
                            # Preserve existing non-empty fields
                            for field_k, field_v in v.items():
                                if field_v is not None or field_k not in merged[k]:
                                    merged[k][field_k] = field_v

            response = self.session.put(url, json=merged, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Firebase update_boss_states failed: {e}")
            return False

    def update_boss_rules(self, rules):
        """Upload current boss rules."""
        url = self._get_url("boss_rules")
        if not url:
            return False
        try:
            response = self.session.put(url, json=rules, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Firebase update_boss_rules failed: {e}")
            return False

    def push_chat_logs(self, logs):
        """Upload chat history list."""
        url = self._get_url("chat_history")
        if not url:
            return False
        try:
            # We overwrite the chat history with the latest buffer (e.g. last 100 messages)
            response = self.session.put(url, json=logs, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Firebase push_chat_logs failed: {e}")
            return False

    def get_subscriptions(self):
        """
        Fetch push notification subscription tokens from Firebase.
        Returns a dict of subscriber subscriptions or empty dict.
        """
        url = self._get_url("subscriptions")
        if not url:
            return {}
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data if data else {}
            return {}
        except Exception as e:
            logger.error(f"Firebase get_subscriptions failed: {e}")
            return {}

    def get_reports(self):
        """
        Fetch pending manual death reports submitted by users.
        Returns a dict of reports or empty dict.
        """
        url = self._get_url("reports")
        if not url:
            return {}
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data if data else {}
            return {}
        except Exception as e:
            logger.error(f"Firebase get_reports failed: {e}")
            return {}

    def delete_report(self, report_id):
        """Delete a specific report after processing it."""
        url = self._get_url(f"reports/{report_id}")
        if not url:
            return False
        try:
            response = self.session.delete(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Firebase delete_report failed: {e}")
            return False

    def clear_all_reports(self):
        """Clear the entire reports node."""
        url = self._get_url("reports")
        if not url:
            return False
        try:
            response = self.session.delete(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Firebase clear_all_reports failed: {e}")
            return False

    def delete_boss_state(self, boss_name):
        """Delete a specific boss state from Firebase Realtime Database."""
        if not boss_name:
            return False
        import urllib.parse
        encoded_key = urllib.parse.quote(str(boss_name).strip())
        url = self._get_url(f"boss_states/{encoded_key}")
        if not url:
            return False
        try:
            response = self.session.delete(url, timeout=5)
            logger.info(f"Deleted Firebase boss state for '{boss_name}': HTTP {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Firebase delete_boss_state failed for '{boss_name}': {e}")
            return False

    def purge_stale_boss_states(self, active_rules):
        """Purge any boss state in Firebase that is not present in active_rules."""
        if not self.is_configured() or not active_rules:
            return
        active_names = set(r["name"] for r in active_rules if "name" in r)
        url = self._get_url("boss_states")
        if not url:
            return
        try:
            res = self.session.get(url, timeout=5)
            if res.status_code == 200 and res.json():
                states = res.json()
                import urllib.parse
                for k, v in states.items():
                    decoded_k = urllib.parse.unquote(k)
                    boss_name = (v.get("name") if isinstance(v, dict) else None) or decoded_k
                    if boss_name and boss_name not in active_names:
                        logger.info(f"Purging stale boss state '{boss_name}' from Firebase")
                        self.delete_boss_state(k)
        except Exception as e:
            logger.error(f"Failed to purge stale boss states: {e}")
