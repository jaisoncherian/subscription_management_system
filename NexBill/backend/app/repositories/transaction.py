"""Transaction boundaries, so services do not touch the session directly."""
from app.extensions import db


def commit() -> None:
    db.session.commit()


def rollback() -> None:
    db.session.rollback()


def savepoint():
    """A context manager. An exception inside undoes only the work inside it."""
    return db.session.begin_nested()
