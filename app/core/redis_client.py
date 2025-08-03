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

    def add_to_blacklist(self, jti: str, expires_in: int = None) -> bool:
        """
        Add a JWT token ID to the blacklist

        Args:
            jti: JWT ID to blacklist
            expires_in: Time in seconds until the blacklist entry expires (optional)

        Returns:
            bool: True if successfully added, False otherwise
        """
        try:
            if expires_in:
                return self.redis_client.setex(f"blacklist:{jti}", expires_in, "1")
            else:
                return self.redis_client.set(f"blacklist:{jti}", "1")
        except Exception as e:
            print(f"Error adding to blacklist: {e}")
            return False

    def is_blacklisted(self, jti: str) -> bool:
        """
        Check if a JWT token ID is blacklisted

        Args:
            jti: JWT ID to check

        Returns:
            bool: True if blacklisted, False otherwise
        """
        try:
            return self.redis_client.exists(f"blacklist:{jti}") > 0
        except Exception as e:
            print(f"Error checking blacklist: {e}")
            return False

    def store_token_pair(
        self, access_jti: str, refresh_jti: str, expires_in: int
    ) -> bool:
        """
        Store the relationship between access token and refresh token JTIs

        Args:
            access_jti: Access token JTI
            refresh_jti: Refresh token JTI
            expires_in: Time in seconds until the mapping expires

        Returns:
            bool: True if successfully stored, False otherwise
        """
        try:
            # Store bidirectional mapping
            self.redis_client.setex(
                f"token_pair:access:{access_jti}", expires_in, refresh_jti
            )
            self.redis_client.setex(
                f"token_pair:refresh:{refresh_jti}", expires_in, access_jti
            )
            return True
        except Exception as e:
            print(f"Error storing token pair: {e}")
            return False

    def get_paired_token(self, jti: str, token_type: str) -> str:
        """
        Get the paired token JTI for a given token

        Args:
            jti: JWT ID to find pair for
            token_type: 'access' or 'refresh'

        Returns:
            str: Paired token JTI or None if not found
        """
        try:
            return self.redis_client.get(f"token_pair:{token_type}:{jti}")
        except Exception as e:
            print(f"Error getting paired token: {e}")
            return None

    def blacklist_token_pair(self, jti: str, token_type: str, expires_in: int) -> bool:
        """
        Blacklist both tokens in a pair

        Args:
            jti: JWT ID of one token in the pair
            token_type: 'access' or 'refresh' - type of the provided JTI
            expires_in: Time in seconds until the blacklist entries expire

        Returns:
            bool: True if successfully blacklisted both tokens, False otherwise
        """
        try:
            # Blacklist the current token
            self.add_to_blacklist(jti, expires_in)

            # Find and blacklist the paired token
            paired_jti = self.get_paired_token(jti, token_type)
            if paired_jti:
                self.add_to_blacklist(paired_jti, expires_in)

                # Clean up the token pair mappings
                self.redis_client.delete(
                    f"token_pair:access:{jti if token_type == 'access' else paired_jti}"
                )
                self.redis_client.delete(
                    f"token_pair:refresh:{jti if token_type == 'refresh' else paired_jti}"
                )

            return True
        except Exception as e:
            print(f"Error blacklisting token pair: {e}")
            return False

    def remove_token_pair(self, access_jti: str, refresh_jti: str) -> bool:
        """
        Remove token pair mapping (used when replacing tokens)

        Args:
            access_jti: Access token JTI
            refresh_jti: Refresh token JTI

        Returns:
            bool: True if successfully removed, False otherwise
        """
        try:
            self.redis_client.delete(f"token_pair:access:{access_jti}")
            self.redis_client.delete(f"token_pair:refresh:{refresh_jti}")
            return True
        except Exception as e:
            print(f"Error removing token pair: {e}")
            return False


# Global Redis client instance
redis_client = RedisClient()
