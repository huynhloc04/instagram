from sqlalchemy import select

from app.v1.models.user import User


class UserRepository:
    """
    Data access layer for User model.

    Uses scoped_session to automatically get the current thread's session.
    Does NOT manage transactions - that's the service layer's responsibility.
    All methods use the current thread's session from the scoped_session registry.
    """

    def __init__(self, session_factory):
        self.session = session_factory()

    def create(self, user: User) -> None:
        """Add user to the current session"""
        self.session.add(user)

    def get_by_email(self, email: str) -> User | None:
        """Get user by email using current session"""
        smt = select(User).where(User.email == email)
        return self.session.execute(smt).scalar_one_or_none()

    def get_by_username(self, username: str) -> User | None:
        """Get user by username using current session"""
        smt = select(User).where(User.username == username)
        return self.session.execute(smt).scalar_one_or_none()

    def get_by_id(self, id: int) -> User | None:
        """Get user by id using current session"""
        smt = select(User).where(User.id == id)
        return self.session.execute(smt).scalar_one_or_none()
