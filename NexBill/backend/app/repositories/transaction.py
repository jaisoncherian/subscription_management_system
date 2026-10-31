"""Transaction boundaries, so services do not touch the session directly."""
from app.extensions import db


def commit() -> None:
    db.session.commit()


def rollback() -> None:
    db.session.rollback()
