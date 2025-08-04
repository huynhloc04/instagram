import redis
from datetime import datetime

from app.core.config import settings


class RedisClient:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )

    def add_to_blacklist(self, jit: str, expires_in: int = None) -> bool:
        """
        Add a JWT token ID to the blacklist

        Args:
            jit: JWT ID to blacklist
            expires_in: Time in seconds until the blacklist entry expires (optional)

        Returns:
            bool: True if successfully added, False otherwise
        """
        try:
            if expires_in:
                return self.redis_client.setex(f"blacklist:{jit}", expires_in, "1")
            else:
                return self.redis_client.set(f"blacklist:{jit}", "1")
        except Exception as e:
            print(f"Error adding to blacklist: {e}")
            return False

    def is_blacklisted(self, jit: str) -> bool:
        """
        Check if a JWT token ID is blacklisted

        Args:
            jit: JWT ID to check

        Returns:
            bool: True if blacklisted, False otherwise
        """
        try:
            return self.redis_client.exists(f"blacklist:{jit}")
        except Exception as e:
            print(f"Error checking blacklist: {e}")
            return False

    def add_to_logout_all_devices(self, user_id: str) -> bool:
        """
        Add a user ID to the logout all devices list. Mark the time of logout all devices.
        Args:
            user_id: User ID to add
        Returns:
            bool: True if successfully added, False otherwise
        """
        try:
            expires_in = int(settings.JWT_REFRESH_TOKEN_EXPIRES)
            return self.redis_client.setex(
                f"logout_all_devices:{user_id}",
                expires_in,
                int(datetime.now().timestamp()),
            )
        except Exception as e:
            print(f"Error adding to logout all devices: {e}")
            return False

    def is_logout_all_devices(self, user_id: str, iat: int) -> bool:
        """
        Check if a user ID is in the logout all devices list
        Args:
            user_id: User ID to check
            iat: time of created_at of the token
        Returns:
            bool: True if the current token is created before the last logout all devices, False otherwise
        """
        try:
            last_logout_all_devices = self.redis_client.get(
                f"logout_all_devices:{user_id}"
            )
            if last_logout_all_devices and int(last_logout_all_devices) > iat:
                return int(last_logout_all_devices) > iat
            return False
        except Exception as e:
            print(f"Error checking logout all devices: {e}")
            return False


# Global Redis client instance
redis_client = RedisClient()
