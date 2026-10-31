"""Route decorators."""
from functools import wraps

from flask_jwt_extended import get_current_user, verify_jwt_in_request

from app.core.errors import Forbidden


def roles_required(*roles):
    """Require a logged-in, active user whose role is one of `roles`.

    The role comes from the database, not from the token.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            if get_current_user().role not in roles:
                raise Forbidden()
            return fn(*args, **kwargs)

        return wrapper

    return decorator
