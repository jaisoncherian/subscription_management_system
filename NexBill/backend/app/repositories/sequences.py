"""Database sequences, used for human-readable document numbers."""
from sqlalchemy import Sequence

from app.extensions import db


def next_value(sequence: Sequence) -> int:
    return db.session.scalar(sequence.next_value())
