from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.v1.models.base import BaseModel


class EmailJob(BaseModel):
    """
        Handle email sending idempotency using UNIQUE key
    """
    __tablename__ = "email_job"
    idempotency_key: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=True
    )
    is_sent: Mapped[Boolean] = mapped_column(String(10), nullable=True)
