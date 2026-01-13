from sqlalchemy import create_engine
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker, scoped_session


class Database:
    def __init__(self, db_url: str) -> None:
        self.engine = create_engine(
            db_url,
            pool_recycle=3600,   # Expiration timer (in seconds) for a connection.
            pool_size=10,        # Initialize a pool with 10 connections
            max_overflow=20,     # If number of connections reaches 10, open additional 20 connections.
            pool_pre_ping=True,  # Sends a tiny "ping" (like SELECT 1) to the database to see if it's still alive before connecting.
        )
        self.session_factory = scoped_session(
            sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
                expire_on_commit=False,
            ),
        )

    def shutdown(self):
        """
            Manage Application Lifecycle - Teardown, close all connections gracefully
        """
        self.engine.dispose()

    @contextmanager
    def session(self):
        """
            Transaction context manager for request lifecycle.
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            # Remove session from registry (closes it and clears thread-local storage)
            self.session_factory.remove()
