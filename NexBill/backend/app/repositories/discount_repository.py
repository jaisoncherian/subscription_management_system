"""Discount usage."""
from app.extensions import db
from app.models import Discount


def claim(discount: Discount) -> bool:
    """Take one use of the discount. Returns False if none are left.

    The limit is checked inside the UPDATE, so that simultaneous claims cannot
    go past it however many billing runs overlap.
    """
    result = db.session.execute(
        db.update(Discount)
        .where(
            Discount.id == discount.id,
            Discount.is_active.is_(True),
            db.or_(
                Discount.usage_limit.is_(None),
                Discount.usage_count < Discount.usage_limit,
            ),
        )
        .values(usage_count=Discount.usage_count + 1)
        .execution_options(synchronize_session=False)
    )
    db.session.expire(discount)
    return result.rowcount == 1
