"""Readiness checks."""
import logging

from sqlalchemy.exc import SQLAlchemyError

from app.repositories import transaction

logger = logging.getLogger(__name__)


def database_is_reachable() -> bool:
    try:
        transaction.ping()
        return True
    except SQLAlchemyError as error:
        logger.error("database is not reachable: %s", type(error).__name__)
        transaction.rollback()
        return False
