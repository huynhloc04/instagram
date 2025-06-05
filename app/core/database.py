from typing import Iterator

from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import InternalServerError
from sqlalchemy.orm import Session
from flask import current_app

from app.core.extensions import db


@contextmanager
def db_session() -> Iterator[Session]:
    session = db.session
    try:
        yield session
    except SQLAlchemyError as error:
        session.rollback()
        raise InternalServerError(str(error))
    finally:
        session.close()
