from app.core.extensions import db

from app.v1.models.base import BaseModel


class Tag(BaseModel):
    __tablename__ = "tags"

    tag_name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"{self.name}"
