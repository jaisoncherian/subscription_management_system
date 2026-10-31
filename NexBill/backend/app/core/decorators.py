"""Route decorators."""
from functools import wraps

from flask_jwt_extended import get_jwt, verify_jwt_in_request

from app.core.errors import Forbidden


def roles_required(*roles):
    """Require a valid JWT whose "roles" claim contains at least one of `roles`.

    The auth feature must issue tokens with a "roles" claim holding a list of
    strings, e.g. create_access_token(identity=..., additional_claims={"roles": ["admin"]}).
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            if not set(roles) & set(get_jwt().get("roles", [])):
                raise Forbidden()
            return fn(*args, **kwargs)

        return wrapper

    return decorator
