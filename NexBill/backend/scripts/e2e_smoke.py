"""End-to-end proof of the business workflow, against a running server.

Standard library only. Uses the cookie session and CSRF header the frontend uses.
Stops at the first failed check and exits with a non-zero code.

    python scripts/e2e_smoke.py [--base-url http://localhost:5173]

Reads ADMIN_EMAIL and ADMIN_PASSWORD from the environment or NexBill/.env, so run
`flask create-admin` first. It creates data, so point the server at a database you
do not mind filling. Names include a run id, so it can be run more than once. Allow
a minute between runs, because login is limited to 5 per minute.
"""
import argparse
import http.cookiejar
import json
import os
import secrets
import sys
import urllib.error
import urllib.request
from datetime import date
from decimal import Decimal
from pathlib import Path

RUN = secrets.token_hex(3)
# Generated per run: satisfies the password rule and is never printed.
PASSWORD = f"Aa!{secrets.token_urlsafe(16)}"


class Failed(Exception):
    pass


def check(condition, label, detail=None):
    if not condition:
        raise Failed(f"{label}{f': {detail}' if detail is not None else ''}")
    print(f"  ok  {label}")


class Response:
    def __init__(self, status, raw, content_type):
        self.status = status
        self.text = raw.decode("utf-8", "replace")
        self.content_type = content_type

    @property
    def json(self):
        return json.loads(self.text)

    @property
    def code(self):
        return self.json["error"]["code"]


class Session:
    """One browser: a cookie jar, and the CSRF header on every write."""

    def __init__(self, base_url):
        self.base_url = base_url
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def _csrf(self):
        return next((c.value for c in self.jar if c.name == "csrf_access_token"), None)

    def request(self, method, path, body=None, csrf=True):
        headers = {"Accept": "application/json"}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        if csrf and method != "GET" and self._csrf():
            headers["X-CSRF-TOKEN"] = self._csrf()
        request = urllib.request.Request(self.base_url + path, data, headers, method=method)
        try:
            with self.opener.open(request, timeout=30) as reply:
                return Response(reply.status, reply.read(), reply.headers.get("Content-Type", ""))
        except urllib.error.HTTPError as reply:
            return Response(reply.code, reply.read(), reply.headers.get("Content-Type", ""))

    def get(self, path):
        return self.request("GET", path)

    def post(self, path, body=None, csrf=True):
        return self.request("POST", path, body, csrf)

    def login(self, email, password):
        return self.post("/api/auth/login", {"email": email, "password": password})


def expect(response, status, label):
    check(response.status == status, f"{label} -> {status}", f"got {response.status}: {response.text[:300]}")
    return response


def is_money(value):
    return isinstance(value, str) and Decimal(value).as_tuple().exponent == -2


def admin_credentials():
    values = {}
    env_file = Path(__file__).resolve().parents[2] / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip("'\"")
    email = os.getenv("ADMIN_EMAIL", values.get("ADMIN_EMAIL"))
    password = os.getenv("ADMIN_PASSWORD", values.get("ADMIN_PASSWORD"))
    if not email or not password:
        raise Failed("Set ADMIN_EMAIL and ADMIN_PASSWORD")
    return email, password


def step(title):
    print(f"\n{title}")


def run(base_url):
    new = lambda: Session(base_url)
    customer_email = f"e2e.customer.{RUN}@example.com"

    step("0. Server is up, and pages are fetched through the configured URL")
    expect(new().get("/api/health"), 200, "GET /api/health")

    step("1. Customer registers")
    public = new()
    weak = expect(
        public.post("/api/auth/register", {"email": customer_email, "password": "weak", "full_name": "E2E Customer"}),
        422, "weak password",
    )
    check("password" in weak.json["error"]["fields"], "error names the password field")
    created = expect(
        public.post(
            "/api/auth/register",
            {"email": customer_email.upper(), "password": PASSWORD, "full_name": "E2E Customer", "role": "admin"},
        ),
        201, "valid registration",
    ).json
    check(created["role"] == "customer", "role in the body is ignored, role=customer", created["role"])
    check(created["email"] == customer_email, "email is stored in lower case", created["email"])
    check("password_hash" not in created, "no password hash in the response")
    duplicate = expect(
        public.post("/api/auth/register", {"email": customer_email, "password": PASSWORD, "full_name": "Again"}),
        409, "duplicate email",
    )
    check(duplicate.code == "email_taken", "code is email_taken", duplicate.code)
    known = expect(public.post("/api/auth/forgot-password", {"email": customer_email}), 200, "forgot-password, known email")
    unknown = expect(
        public.post("/api/auth/forgot-password", {"email": f"nobody.{RUN}@example.com"}),
        200, "forgot-password, unknown email",
    )
    check(known.text == unknown.text, "both replies are identical")

    step("2. Customer logs in, with no access to staff areas")
    customer = new()
    bad = expect(customer.login(customer_email, "Wrong!Password1"), 401, "wrong password")
    check(bad.code == "invalid_credentials", "code is invalid_credentials", bad.code)
    me = expect(customer.login(customer_email, PASSWORD), 200, "login").json
    check(me["role"] == "customer", "role=customer", me["role"])
    cookies = {c.name: c for c in customer.jar}
    check("access_token_cookie" in cookies and "csrf_access_token" in cookies, "session and CSRF cookies are set")
    check(cookies["access_token_cookie"].has_nonstandard_attr("HttpOnly"), "access token cookie is httpOnly")
    check(expect(customer.get("/api/auth/me"), 200, "GET /api/auth/me").json["id"] == me["id"], "me is this user")
    expect(customer.get("/api/customers"), 403, "GET /api/customers")
    expect(customer.get("/api/reports/summary"), 403, "GET /api/reports/summary")
    expect(customer.post("/api/taxes", {"name": "x", "rate": "1"}), 403, "POST /api/taxes")

    step("3. Admin sets up staff and the catalog")
    admin_email, admin_password = admin_credentials()
    admin = new()
    check(expect(admin.login(admin_email, admin_password), 200, "admin login").json["role"] == "admin", "role=admin")
    expect(admin.post("/api/taxes", {"name": f"No CSRF {RUN}", "rate": "1.00"}, csrf=False), 401, "write without CSRF header")
    staff_email = f"e2e.staff.{RUN}@example.com"
    staff_user = expect(
        admin.post(
            "/api/staff",
            {"email": staff_email, "password": PASSWORD, "full_name": "E2E Staff", "staff_function": "sales_rep"},
        ),
        201, "create staff",
    ).json
    check(staff_user["role"] == "staff", "role=staff", staff_user["role"])
    tax = expect(admin.post("/api/taxes", {"name": f"GST {RUN}", "rate": "18.00"}), 201, "create tax").json
    product = expect(
        admin.post(
            "/api/products",
            {
                "name": f"Hosting {RUN}",
                "sales_price": "1000.00",
                "variants": [{"attribute": "Brand", "value": "Odoo", "extra_price": "560.00"}],
            },
        ),
        201, "create product with Brand=Odoo, extra 560",
    ).json
    variant = product["variants"][0]
    check(variant["extra_price"] == "560.00", "variant extra is 560.00", variant["extra_price"])
    plan = expect(
        admin.post(
            "/api/plans",
            {"name": f"Monthly {RUN}", "billing_period": "monthly", "is_pausable": True, "is_renewable": True},
        ),
        201, "create plan",
    ).json
    discount = expect(
        admin.post(
            "/api/discounts",
            {"code": f"E2E{RUN}", "name": "E2E 10%", "discount_type": "percent", "value": "10.00", "usage_limit": 1},
        ),
        201, "create percent discount with usage limit 1",
    ).json

    step("4. A template, then a subscription from it")
    staff = new()
    check(expect(staff.login(staff_email, PASSWORD), 200, "staff login").json["role"] == "staff", "role=staff")
    template_body = {
        "name": f"Standard {RUN}",
        "plan_id": plan["id"],
        "validity_days": 30,
        "lines": [{"product_id": product["id"], "variant_id": variant["id"], "tax_id": tax["id"], "quantity": 2}],
    }
    # docs/API.md and the tests make templates admin-only, so staff is refused.
    expect(staff.post("/api/quotation-templates", template_body), 403, "staff creating a template (admin only)")
    template = expect(admin.post("/api/quotation-templates", template_body), 201, "admin creates template").json
    listed = expect(staff.get("/api/customers?page_size=100&page=1"), 200, "staff lists customers").json
    check(set(listed) == {"items", "page", "page_size", "total"}, "page shape", sorted(listed))
    # The newest customer can be past the first page on a database with many customers.
    last_page = max(1, (listed["total"] + 99) // 100)
    rows = expect(staff.get(f"/api/customers?page_size=100&page={last_page}"), 200, "last page of customers").json["items"]
    row = next((c for c in rows if c["email"] == customer_email), None)
    check(row is not None and set(row) == {"id", "name", "email"}, "customer is listed with id, name, email only", row)
    expect(staff.get("/api/customers?page_size=101"), 422, "page_size above 100")
    subscription = expect(
        staff.post(
            "/api/subscriptions",
            {"customer_id": row["id"], "template_id": template["id"], "discount_id": discount["id"]},
        ),
        201, "staff creates subscription",
    ).json
    url = f"/api/subscriptions/{subscription['id']}"
    check(subscription["status"] == "draft", "starts as draft", subscription["status"])
    check(subscription["allowed_actions"] == ["send-quotation"], "allowed_actions", subscription["allowed_actions"])
    line = subscription["lines"][0]
    check(line["unit_price"] == "1560.00", "unit price is 1000 + 560", line["unit_price"])
    check(line["amount"] == "3120.00", "line amount is 1560 x 2", line["amount"])

    step("5. Subscription state machine")
    jump = expect(staff.post(f"{url}/activate"), 409, "activate straight from draft")
    check(jump.code == "invalid_transition", "code is invalid_transition", jump.code)
    expect(customer.post(f"{url}/send-quotation"), 403, "customer attempting an action")
    for action, status, allowed in (
        ("send-quotation", "quotation", ["confirm"]),
        ("confirm", "confirmed", ["activate"]),
    ):
        body = expect(staff.post(f"{url}/{action}"), 200, action).json
        check(body["status"] == status and body["allowed_actions"] == allowed, f"now {status}, allows {allowed}", body["status"])
    active = expect(staff.post(f"{url}/activate"), 200, "activate").json
    check(active["status"] == "active", "now active", active["status"])
    check(active["next_billing_date"] == date.today().isoformat(), "bills from today (YYYY-MM-DD)", active["next_billing_date"])
    check(set(active["allowed_actions"]) == {"pause", "close"}, "pause and close offered; renew needs an expiry", active["allowed_actions"])

    step("6. Billing, run twice")
    expect(staff.post("/api/billing/run"), 403, "staff running billing (admin only)")
    first = expect(admin.post("/api/billing/run"), 200, "first billing run").json
    check(first["invoices_created"] >= 1 and first["failures"] == 0, "created invoices, no failures", first)
    second = expect(admin.post("/api/billing/run"), 200, "second billing run").json
    check(second["invoices_created"] == 0 and second["failures"] == 0, "second run creates nothing", second)
    invoices = expect(admin.get(f"/api/invoices?customer_id={row['id']}&page_size=100"), 200, "list customer's invoices").json
    check(invoices["total"] == 1, "exactly one invoice, so no double billing", invoices["total"])
    invoice_url = f"/api/invoices/{invoices['items'][0]['id']}"
    discounts = expect(admin.get("/api/discounts?page_size=100"), 200, "list discounts").json["items"]
    used = next(d for d in discounts if d["id"] == discount["id"])
    check(used["usage_count"] == 1, "discount usage counted once", used["usage_count"])

    step("7. Invoice amounts and visibility")
    invoice = expect(admin.get(invoice_url), 200, "GET invoice").json
    # 3120.00 less 10% = 2808.00, plus 18% tax on that = 505.44.
    check(invoice["subtotal"] == "3120.00", "subtotal 3120.00", invoice["subtotal"])
    check(invoice["discount_total"] == "312.00", "discount 312.00", invoice["discount_total"])
    check(invoice["tax_total"] == "505.44", "tax 505.44", invoice["tax_total"])
    check(invoice["total"] == "3313.44", "total 3313.44", invoice["total"])
    check(all(is_money(invoice[k]) for k in ("subtotal", "discount_total", "tax_total", "total", "amount_paid", "balance_due")), "money values are strings")
    check(invoice["status"] == "draft", "lower-case status: draft", invoice["status"])
    check(invoice["allowed_actions"] == ["confirm", "cancel"], "allowed_actions", invoice["allowed_actions"])
    check(expect(customer.get("/api/portal/invoices"), 200, "portal invoices").json["total"] == 0, "customer cannot see the draft")
    expect(customer.get(invoice_url), 404, "customer reading the draft directly")
    expect(staff.post(f"{invoice_url}/payments", {"method": "card", "amount": "1.00"}), 409, "payment on a draft")

    step("8. Confirm, pay in two parts, and print")
    confirmed = expect(staff.post(f"{invoice_url}/confirm"), 200, "confirm invoice").json
    check(confirmed["allowed_actions"] == ["cancel", "send", "pay"], "allowed_actions", confirmed["allowed_actions"])
    portal = expect(customer.get("/api/portal/invoices"), 200, "portal invoices").json
    check(set(portal) == {"items", "page", "page_size", "total"}, "page shape", sorted(portal))
    check(portal["total"] == 1 and portal["items"][0]["total"] == "3313.44", "customer now sees it", portal["items"])
    expect(staff.post(f"{invoice_url}/send"), 200, "send invoice")
    over = expect(staff.post(f"{invoice_url}/payments", {"method": "card", "amount": "3313.45"}), 409, "overpayment")
    check(over.code == "overpayment", "code is overpayment", over.code)
    expect(staff.post(f"{invoice_url}/payments", {"method": "card", "amount": "0"}), 422, "zero payment")
    part = expect(staff.post(f"{invoice_url}/payments", {"method": "upi", "amount": "1000.00"}), 201, "part payment").json
    check(part["amount"] == "1000.00", "amount is a string", part["amount"])
    half = expect(staff.get(invoice_url), 200, "invoice after part payment").json
    check(half["status"] == "confirmed" and half["balance_due"] == "2313.44", "still confirmed, balance 2313.44", half["balance_due"])
    check("cancel" not in half["allowed_actions"], "cancel is no longer offered")
    expect(staff.post(f"{invoice_url}/cancel"), 409, "cancel with a payment recorded")
    expect(staff.post(f"{invoice_url}/payments", {"method": "bank_transfer", "amount": "2313.44"}), 201, "final payment")
    paid = expect(staff.get(invoice_url), 200, "invoice after final payment").json
    check(paid["status"] == "paid" and paid["balance_due"] == "0.00", "paid in full", paid["status"])
    check(paid["allowed_actions"] == ["send"], "only send is left", paid["allowed_actions"])
    printed = expect(customer.get(f"{invoice_url}/print"), 200, "customer prints invoice")
    check("text/html" in printed.content_type and paid["invoice_number"] in printed.text, "HTML holds the invoice number")

    step("9. Portal and reports use the real data")
    subs = expect(customer.get("/api/portal/subscriptions"), 200, "portal subscriptions").json
    check(subs["total"] == 1 and subs["items"][0]["status"] == "active", "customer sees the active subscription", subs["items"])
    summary = expect(staff.get("/api/reports/summary"), 200, "reports summary").json
    check(summary["active_subscriptions"] >= 1, "counts active subscriptions", summary)
    check(all(is_money(summary[k]) for k in ("mrr", "revenue_collected", "outstanding")), "money values are strings", summary)
    check(Decimal(summary["mrr"]) >= Decimal("3120.00"), "MRR includes 3120.00", summary["mrr"])
    check(Decimal(summary["revenue_collected"]) >= Decimal("3313.44"), "revenue includes 3313.44", summary["revenue_collected"])
    today = date.today().isoformat()
    ranged = expect(staff.get(f"/api/reports/summary?date_from={today}&date_to={today}"), 200, "summary for today").json
    check(Decimal(ranged["revenue_collected"]) >= Decimal("3313.44"), "date range includes today's payments", ranged)
    revenue = expect(staff.get("/api/reports/revenue?group=month"), 200, "reports revenue").json
    this_month = today[:8] + "01"
    check(any(r["period"] == this_month and is_money(r["collected"]) for r in revenue), "this month is in the revenue report", revenue)
    expect(staff.get("/api/reports/overdue?page=1&page_size=5"), 200, "reports overdue")

    step("10. Another customer sees none of it")
    other_email = f"e2e.other.{RUN}@example.com"
    expect(public.post("/api/auth/register", {"email": other_email, "password": PASSWORD, "full_name": "Other"}), 201, "register second customer")
    other = new()
    expect(other.login(other_email, PASSWORD), 200, "second customer login")
    expect(other.get(url), 404, "their subscription")
    expect(other.get(invoice_url), 404, "their invoice")
    expect(other.get(f"{invoice_url}/print"), 404, "their printable invoice")
    check(expect(other.get("/api/portal/invoices"), 200, "own portal").json["total"] == 0, "no invoices in the portal")

    step("11. Pause, resume, close, and log out")
    check(expect(staff.post(f"{url}/pause"), 200, "pause").json["status"] == "paused", "now paused")
    check(expect(staff.post(f"{url}/resume"), 200, "resume").json["status"] == "active", "active again")
    closed = expect(staff.post(f"{url}/close"), 200, "close").json
    check(closed["status"] == "closed" and closed["allowed_actions"] == [], "closed, with no actions left", closed["status"])
    expect(customer.post("/api/auth/logout"), 200, "logout")
    gone = expect(customer.get("/api/auth/me"), 401, "GET /api/auth/me after logout")
    check(set(gone.json["error"]) == {"code", "message", "fields"}, "error has the standard shape")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    args = parser.parse_args()
    print(f"Target: {args.base_url}  (run {RUN})")
    try:
        run(args.base_url.rstrip("/"))
    except Failed as failure:
        print(f"\nFAILED: {failure}")
        return 1
    print("\nALL STEPS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
