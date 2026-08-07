import logging
import json
import base64
import requests
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from pywebpush import webpush, WebPushException

logger = logging.getLogger(__name__)

class WebPushManager:
    def __init__(self, private_key_pem=None):
        self.private_key_pem = private_key_pem
        self.public_key_b64 = None
        self._session = requests.Session()
        
        if self.private_key_pem:
            try:
                self._load_public_key()
            except Exception as e:
                logger.error(f"Failed to load public key from PEM: {e}")
                self.private_key_pem = None

        if not self.private_key_pem:
            self.generate_keys()

    def close(self):
        """Close the persistent HTTP session."""
        try:
            self._session.close()
        except Exception:
            pass

    def generate_keys(self):
        """Generate a new VAPID EC key pair."""
        try:
            private_key = ec.generate_private_key(ec.SECP256R1())
            
            # Export private key in PEM format
            self.private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')
            
            self._load_public_key()
            logger.info("Generated new VAPID key pair successfully.")
        except Exception as e:
            logger.error(f"Failed to generate VAPID keys: {e}")

    def _load_public_key(self):
        """Derive and serialize public key from private key PEM."""
        private_key = serialization.load_pem_private_key(
            self.private_key_pem.encode('utf-8'),
            password=None
        )
        public_key = private_key.public_key()
        
        # Serialize to X9.62 uncompressed point format (required for Web Push public key)
        public_der = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        # Web Push requires base64url encoding without padding
        self.public_key_b64 = base64.urlsafe_b64encode(public_der).decode('utf-8').rstrip('=')

    def send_notification(self, subscription_info, title, body):
        """
        Send a web push notification to a single subscriber.
        Returns: (success_boolean, status_message)
        Status message will be "expired" if subscription is no longer valid.
        """
        if not self.private_key_pem:
            return False, "VAPID private key is not initialized."

        payload = {
            "title": title,
            "body": body,
            "timestamp": None  # Can add metadata if needed
        }

        try:
            response = webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=self.private_key_pem,
                vapid_claims={
                    "sub": "mailto:lineagew-chat-capture@example.com"
                },
                requests_session=self._session,
                timeout=5
            )
            return True, "Success"
        except WebPushException as ex:
            # Check if subscription has expired or is invalid
            if ex.response is not None and ex.response.status_code in [404, 410]:
                logger.info(f"Subscription expired (status {ex.response.status_code}). Removing subscriber.")
                return False, "expired"
            logger.error(f"WebPushException sending notification: {ex}")
            return False, str(ex)
        except Exception as e:
            logger.error(f"Generic error sending web push: {e}")
            return False, str(e)

    def send_to_all(self, subscriptions, title, body, expired_callback=None):
        """
        Send push notifications to all subscribers.
        subscriptions: Dict of subscription objects from Firebase (subscriptionId -> subscription dict)
        expired_callback: Function taking (subscription_id) to delete it from Firebase if expired
        """
        if not subscriptions:
            return 0, 0

        success_count = 0
        failure_count = 0

        # subscriptions is a dict where keys are IDs and values are subscription details
        for sub_id, sub_info in list(subscriptions.items()):
            # Ensure sub_info is a dictionary and contains required keys
            if not isinstance(sub_info, dict) or "endpoint" not in sub_info:
                continue

            success, status = self.send_notification(sub_info, title, body)
            if success:
                success_count += 1
            else:
                failure_count += 1
                if status == "expired" and expired_callback:
                    try:
                        expired_callback(sub_id)
                    except Exception as e:
                        logger.error(f"Failed to delete expired subscription {sub_id}: {e}")

        logger.info(f"Web Push batch send: {success_count} succeeded, {failure_count} failed.")
        return success_count, failure_count
