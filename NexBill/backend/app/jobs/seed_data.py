"""Demo data for showing the product, created through the real services.

Going through the services means the data obeys every business rule, and invoices
and payments add up. Refuses to run twice. Never prints a password.
"""
from datetime import timedelta

from app.core import clock
from app.models.enums import BillingPeriod
from app.repositories import catalog_repository, user_repository
from app.services import (
    auth_service,
    billing_service,
    catalog_service,
    invoice_service,
    payment_service,
    quotation_service,
    subscription_service,
    user_service,
)
from app.services.billing_periods import add_billing_period

MARKER_PRODUCT = "Odoo Hosting"
STAFF_EMAIL = "sales@nexbill.example"
CUSTOMERS = [
    ("Ana Mathew", "ana@acme.example"),
    ("Rahul Nair", "rahul@northwind.example"),
    ("Priya Menon", "priya@bluepeak.example"),
    ("David Thomas", "david@ferngrove.example"),
    ("Meera Iyer", "meera@solstice.example"),
    ("Arjun Das", "arjun@harbourline.example"),
]
MONTHS_OF_HISTORY = 6
PAYMENT_DELAY = timedelta(days=7)
# Unpaid invoices for this customer become the overdue ones on the dashboard.
LATE_PAYER_INDEX = 1


def seed_demo(admin_email: str, admin_password: str, demo_password: str) -> dict | None:
    """Returns a summary, or None if the demo data already exists."""
    if catalog_repository.get_product_by_name(MARKER_PRODUCT):
        return None

    admin, _ = user_service.ensure_admin(admin_email, admin_password)
    user_service.create_staff(admin.id, STAFF_EMAIL, demo_password, "Sana Kurian", "sales_rep")
    customers = [
        _register_customer(name, email, demo_password) for name, email in CUSTOMERS
    ]
    discount, templates = _create_catalog(admin)

    today = clock.today()
    start_of_history = _months_ago(today, MONTHS_OF_HISTORY - 1)
    subscriptions = {
        "ana": _activate(admin, customers[0], templates["standard"], start_of_history, discount.id),
        "rahul": _activate(admin, customers[1], templates["standard"], _months_ago(today, 4)),
        "priya": _activate(admin, customers[2], templates["premium"], _months_ago(today, 3)),
        "david": _activate(admin, customers[3], templates["annual"], _months_ago(today, 2)),
        "meera": _activate(admin, customers[4], templates["standard"], _months_ago(today, 2)),
        "arjun": _activate(admin, customers[5], templates["premium"], _months_ago(today, 1)),
    }
    _create_pipeline(admin, customers, templates)

    # One run per month, dated that month, so invoices and revenue span the history.
    run_date = start_of_history
    while run_date <= today:
        billing_service.run_billing(admin.id, today=run_date)
        run_date = add_billing_period(run_date, BillingPeriod.MONTHLY, 1, anchor_day=start_of_history.day)
    billing_service.run_billing(admin.id, today=today)

    invoices, payments = _settle_invoices(admin, customers[LATE_PAYER_INDEX], today)

    subscription_service.apply_action(admin, subscriptions["meera"].id, "pause")
    subscription_service.apply_action(admin, subscriptions["arjun"].id, "close")

    return {
        "subscriptions": len(subscriptions) + 3,
        "invoices": invoices,
        "payments": payments,
        "staff_email": STAFF_EMAIL,
        "customer_email": CUSTOMERS[0][1],
    }


def _register_customer(name: str, email: str, password: str):
    user = auth_service.register_customer(email, password, name)
    return user_repository.get_customer_for_user(user.id)


def _create_catalog(admin):
    gst_18 = catalog_service.create_tax(admin, name="GST 18%", rate="18.00")
    gst_5 = catalog_service.create_tax(admin, name="GST 5%", rate="5.00")
    hosting = catalog_service.create_product(
        admin,
        name=MARKER_PRODUCT,
        sales_price="1000.00",
        description="Managed hosting",
        variants=[
            {"attribute": "Brand", "value": "Odoo", "extra_price": "560.00"},
            {"attribute": "Brand", "value": "Custom", "extra_price": "250.00"},
        ],
    )
    support = catalog_service.create_product(
        admin, name="Priority Support", sales_price="500.00", variants=[]
    )
    monthly = catalog_service.create_plan(
        admin, name="Monthly", billing_period="monthly", is_pausable=True, is_renewable=True
    )
    yearly = catalog_service.create_plan(
        admin, name="Yearly", billing_period="yearly", is_renewable=True
    )
    discount = catalog_service.create_discount(
        admin,
        product_ids=[],
        code="WELCOME10",
        name="Welcome 10%",
        discount_type="percent",
        value="10.00",
        usage_limit=3,
    )
    odoo = hosting.variants[0]
    line = lambda product, quantity, tax, variant=None: {
        "product_id": product.id,
        "variant_id": variant.id if variant else None,
        "tax_id": tax.id,
        "quantity": quantity,
    }
    templates = {
        "standard": quotation_service.create_template(
            admin, "Standard Hosting", monthly.id, 30, [line(hosting, 2, gst_18, odoo)]
        ),
        "premium": quotation_service.create_template(
            admin,
            "Premium Hosting and Support",
            monthly.id,
            30,
            [line(hosting, 3, gst_18, odoo), line(support, 1, gst_5)],
        ),
        "annual": quotation_service.create_template(
            admin, "Annual Hosting", yearly.id, 45, [line(hosting, 1, gst_18, odoo)]
        ),
    }
    return discount, templates


def _months_ago(today, months: int):
    """The same day of the month, earlier. Day 28 at most, so every month has it."""
    year_month = today.year * 12 + today.month - 1 - months
    return today.replace(year=year_month // 12, month=year_month % 12 + 1, day=min(today.day, 28))


def _activate(admin, customer, template, start_date, discount_id=None):
    subscription = subscription_service.create_from_template(
        admin, customer.id, template.id, start_date=start_date, discount_id=discount_id
    )
    for action in ("send-quotation", "confirm", "activate"):
        subscription_service.apply_action(admin, subscription.id, action)
    return subscription


def _create_pipeline(admin, customers, templates):
    """Subscriptions still in sales, so every stage shows up in the list."""
    draft = subscription_service.create_from_template(admin, customers[2].id, templates["standard"].id)
    quotation = subscription_service.create_from_template(admin, customers[3].id, templates["premium"].id)
    subscription_service.apply_action(admin, quotation.id, "send-quotation")
    confirmed = subscription_service.create_from_template(admin, customers[4].id, templates["annual"].id)
    for action in ("send-quotation", "confirm"):
        subscription_service.apply_action(admin, confirmed.id, action)
    return draft


def _settle_invoices(admin, late_payer, today) -> tuple[int, int]:
    invoices, count = invoice_service.list_invoices(admin, None, None, False, 1, 100)
    payments = 0
    newest_first = sorted(invoices, key=lambda invoice: invoice.id, reverse=True)
    for position, invoice in enumerate(newest_first):
        # The newest invoice stays a draft, to show the step before confirming.
        if position == 0:
            continue
        invoice_service.apply_action(admin, invoice.id, "confirm")
        is_recent = invoice.due_date >= today
        if is_recent or invoice.customer_id == late_payer.id:
            continue
        payment_service.record_payment(
            admin,
            invoice.id,
            "card" if position % 2 else "bank_transfer",
            invoice.total,
            payment_date=min(invoice.invoice_date + PAYMENT_DELAY, today),
        )
        payments += 1
    return count, payments
