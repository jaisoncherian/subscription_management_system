"""The current business date, in one place so that tests and billing agree."""
from datetime import date


def today() -> date:
    return date.today()
