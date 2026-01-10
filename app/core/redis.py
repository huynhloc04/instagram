import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self, settings, redis):
        self.settings = settings
        self.redis = redis

    def add_to_blacklist(self, jit: str, expires_in: int = None) -> bool:
        """Add a JWT token ID to the blacklist"""
        try:
            if expires_in:
                return self.redis.setex(f"blacklist:{jit}", expires_in, "1")
            else:
                return self.redis.set(f"blacklist:{jit}", "1")
        except Exception as e:
            logger.error(f"Error adding to blacklist: {e}")
            return False

    def is_blacklisted(self, jit: str) -> bool:
        """Check if a JWT token ID is blacklisted"""
        try:
            return self.redis.exists(f"blacklist:{jit}")
        except Exception as e:
            logger.error(f"Error checking blacklist: {e}")
            return False

    def logout_all_devices(self, user_id: str) -> bool:
        """Add a user ID to the logout all devices list. Mark the time of logout all devices."""
        try:
            expires_in = int(self.settings.JWT_REFRESH_TOKEN_EXPIRES)
            return self.redis.setex(
                f"logout_all_devices:{user_id}",
                expires_in,
                int(datetime.now().timestamp()),
            )
        except Exception as e:
            logger.error(f"Error adding to logout all devices: {e}")
            return False

    def is_logout_all_devices(self, user_id: str, iat: int) -> bool:
        """Check if a user ID is in the logout all devices list"""
        try:
            last_logout_all_devices = self.redis.get(
                f"logout_all_devices:{user_id}"
            )
            if last_logout_all_devices and int(last_logout_all_devices) > iat:
                return int(last_logout_all_devices) > iat
            return False
        except Exception as e:
            logger.error(f"Error checking logout all devices: {e}")
            return False
