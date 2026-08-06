import logging
import requests
import json
import time

logger = logging.getLogger(__name__)

FIREBASE_API_KEY = "AIzaSyDHKGjbIMXam31tguYnm0ppJZ9fL7YDWBM"

class FirebaseClient:
    def __init__(self, db_url=None, passcode=None, app_check_token=None):
        """
        db_url: Firebase Realtime Database URL, e.g. "https://my-project-default-rtdb.firebaseio.com"
        passcode: The guild password, used as a secure namespace path.
        app_check_token: Optional Firebase App Check token for abuse protection.
        """
        self._db_url = None
        self.db_url = db_url
        self.passcode = passcode if passcode else "default"
        self.app_check_token = app_check_token

        # Anonymous Auth token state
        self._id_token = None
        self._refresh_token_str = None
        self._token_expiry = 0
        
        # Persistent HTTP session for connection pooling and keep-alive
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=5, pool_maxsize=10, max_retries=2)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        if self.app_check_token:
            self.session.headers.update({"X-Firebase-AppCheck": str(self.app_check_token).strip()})

    def sign_in_anonymously(self):
        """Sign in anonymously via Firebase Auth REST API. Returns True on success."""
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
        try:
            resp = self.session.post(url, json={"returnSecureToken": True}, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self._id_token = data.get("idToken")
                self._refresh_token_str = data.get("refreshToken")
                expires_in = int(data.get("expiresIn", 3600))
                self._token_expiry = time.time() + expires_in
                uid = data.get("localId", "unknown")
                logger.info(f"Firebase 匿名登入成功, uid: {uid}")
                return True
            else:
                logger.error(f"Firebase 匿名登入失敗: HTTP {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Firebase 匿名登入例外: {e}")
            return False

    def _refresh_id_token(self):
        """Refresh the id token using the refresh token. Returns True on success."""
        if not self._refresh_token_str:
            return False
        url = f"https://securetoken.googleapis.com/v1/token?key={FIREBASE_API_KEY}"
        try:
            resp = self.session.post(url, json={
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token_str
            }, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self._id_token = data.get("id_token")
                self._refresh_token_str = data.get("refresh_token", self._refresh_token_str)
                expires_in = int(data.get("expires_in", 3600))
                self._token_expiry = time.time() + expires_in
                logger.info("Firebase Auth token 刷新成功")
                return True
            else:
                logger.error(f"Firebase token 刷新失敗: HTTP {resp.status_code}")
                return False
        except Exception as e:
            logger.error(f"Firebase token 刷新例外: {e}")
            return False

    def _get_valid_token(self):
        """Get a valid id token, refreshing or re-signing-in as needed."""
        if self._id_token and time.time() < (self._token_expiry - 300):
            return self._id_token
        # Token expired or about to expire
        if self._refresh_token_str:
            if self._refresh_id_token():
                return self._id_token
        # No refresh token or refresh failed, sign in again
        if self.sign_in_anonymously():
            return self._id_token
        return None

    def set_app_check_token(self, token):
        """Dynamically update App Check token for HTTP requests."""
        self.app_check_token = token
        if token and str(token).strip():
            self.session.headers.update({"X-Firebase-AppCheck": str(token).strip()})
        else:
            self.session.headers.pop("X-Firebase-AppCheck", None)

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
        base = f"{self.db_url}/lineage_w_tracker/{self.passcode}/{path}.json"
        token = self._get_valid_token()
        if token:
            return f"{base}?auth={token}"
        return base

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

    def push_app_check_config(self, site_key):
        """Sync App Check site key to Firebase so Web PWA automatically receives and applies it."""
        url = self._get_url("app_check_config")
        if not url:
            return False
        try:
            response = self.session.put(url, json={"siteKey": site_key}, timeout=5)
            logger.info(f"Pushed App Check config to Firebase: HTTP {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Firebase push_app_check_config failed: {e}")
            return False
