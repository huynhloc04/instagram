import redis
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
            return self.redis_client.exists(f"blacklist:{jit}") > 0
        except Exception as e:
            print(f"Error checking blacklist: {e}")
            return False


# Global Redis client instance
redis_client = RedisClient()
