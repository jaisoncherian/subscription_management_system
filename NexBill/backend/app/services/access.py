"""Who may see which customer's data."""
from app.core.errors import Forbidden
from app.models import User
from app.models.enums import UserRole


def customer_scope(viewer: User) -> int | None:
    """The only customer this viewer may see, or None for staff and admins."""
    if viewer.role != UserRole.CUSTOMER:
        return None
    if viewer.customer is None:
        # Never fall through to None here: that would show everyone's data.
        raise Forbidden()
    return viewer.customer.id
