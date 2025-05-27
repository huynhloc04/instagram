from datetime import datetime

from app.core.extensions import db


class TimeMixin(db.Model):
    __abstract__ = True

    created_at = db.Column(
        "created_at",
        db.Integer, 
        default=lambda: int(datetime.now().timestamp()), 
        nullable=False
    )
    modified_at = db.Column(
        "modified_at",
        db.Integer,
        default=lambda: int(datetime.now().timestamp()), 
        onupdate=lambda: int(datetime.now().timestamp()), 
        nullable=False
    )


class BaseModel(TimeMixin):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
