# NexBill API

Base path: `/api`

## Endpoints

| Method | Path          | Auth | Description  | Success response     |
| ------ | ------------- | ---- | ------------ | -------------------- |
| GET    | `/api/health` | None | The app is running | `200 {"status":"ok"}` |
| GET    | `/api/health/ready` | None | The app can also reach the database | `200 {"status":"ok"}`, or `503` |
| POST   | `/api/auth/register` | None | Public signup. Always creates a customer | `201` user |
| POST   | `/api/auth/login` | None | Log in and set the session cookies | `200` user |
| POST   | `/api/auth/logout` | None | Clear the session cookies | `200 {"message"}` |
| GET    | `/api/auth/me` | Any logged-in user | The current user | `200` user |
| POST   | `/api/auth/forgot-password` | None | Email a reset link. Same reply for any email | `200 {"message"}` |
| POST   | `/api/auth/reset-password` | None | Set a new password with a reset token | `200 {"message"}` |
| POST   | `/api/staff` | Admin | Create a staff account | `201` user |
| GET    | `/api/staff` | Admin | List staff accounts. `?page`, `?page_size` | `200` page |
| POST   | `/api/quotation-templates` | Admin | Create a template | `201` template |
| GET    | `/api/quotation-templates` | Admin, staff | List templates. `?page`, `?page_size`, `?include_inactive=true` | `200` page |
| GET    | `/api/quotation-templates/{id}` | Admin, staff | One template | `200` template |
| PUT    | `/api/quotation-templates/{id}` | Admin | Replace a template. Existing subscriptions do not change | `200` template |
| DELETE | `/api/quotation-templates/{id}` | Admin | Deactivate a template. It is kept, not deleted | `200` template |
| POST   | `/api/subscriptions` | Admin, staff | Create a draft subscription from a template | `201` subscription |
| GET    | `/api/subscriptions` | Any logged-in user | List subscriptions. Customers get only their own. `?status`, `?page`, `?page_size` | `200` page |
| GET    | `/api/subscriptions/{id}` | Any logged-in user | One subscription. Another customer's returns `404` | `200` subscription |
| POST   | `/api/subscriptions/{id}/{action}` | Admin, staff | Change state. No request body | `200` subscription |
| POST   | `/api/billing/run` | Admin | Invoice everything that is due. Same as `flask run-billing` | `200` summary |
| GET    | `/api/invoices` | Any logged-in user | List invoices. Customers get only their own, without drafts. `?status`, `?overdue=true`, `?customer_id`, `?page`, `?page_size` | `200` page |
| GET    | `/api/invoices/{id}` | Any logged-in user | One invoice. Another customer's returns `404` | `200` invoice |
| GET    | `/api/invoices/{id}/print` | Any logged-in user | Printable HTML page. Use the browser to print or save as PDF | `200` HTML |
| POST   | `/api/invoices/{id}/confirm` | Admin, staff | Draft to confirmed. No request body | `200` invoice |
| POST   | `/api/invoices/{id}/cancel` | Admin, staff | Cancel before paid. No request body | `200` invoice |
| POST   | `/api/invoices/{id}/send` | Admin, staff | Email a confirmed or paid invoice. No request body | `200` invoice |
| GET    | `/api/invoices/{id}/payments` | Any logged-in user | Payments on an invoice | `200` list |
| POST   | `/api/invoices/{id}/payments` | Admin, staff | Record a payment | `201` payment |
| GET    | `/api/payments` | Admin, staff | Every payment, newest first, with `invoice_number` and `customer_name`. `?page`, `?page_size` | `200` page |
| GET    | `/api/customers` | Admin, staff | Pick a customer. `?page`, `?page_size`. Each item is `id`, `name`, `email` | `200` page |
| POST   | `/api/taxes` | Admin | Create a tax | `201` tax |
| GET    | `/api/taxes` | Admin, staff | List taxes. `?page`, `?page_size` | `200` page |
| DELETE | `/api/taxes/{id}` | Admin | Deactivate a tax. It is kept, not deleted | `200` tax |
| POST   | `/api/products` | Admin | Create a product with its variants | `201` product |
| GET    | `/api/products` | Admin, staff | List products. `?page`, `?page_size` | `200` page |
| DELETE | `/api/products/{id}` | Admin | Deactivate a product. It is kept, not deleted | `200` product |
| POST   | `/api/plans` | Admin | Create a plan | `201` plan |
| GET    | `/api/plans` | Admin, staff | List plans. `?page`, `?page_size` | `200` page |
| DELETE | `/api/plans/{id}` | Admin | Deactivate a plan. It is kept, not deleted | `200` plan |
| POST   | `/api/discounts` | Admin | Create a discount | `201` discount |
| GET    | `/api/discounts` | Admin, staff | List discounts. `?page`, `?page_size` | `200` page |
| DELETE | `/api/discounts/{id}` | Admin | Deactivate a discount. It is kept, not deleted | `200` discount |
| GET    | `/api/reports/summary` | Admin, staff | Totals. `?date_from`, `?date_to` | `200` summary |
| GET    | `/api/reports/revenue` | Admin, staff | Invoiced and collected per month. `?group=month` is required. `?date_from`, `?date_to` | `200` list |
| GET    | `/api/reports/overdue` | Admin, staff | Overdue invoices. `?date_from`, `?date_to`, `?page`, `?page_size` | `200` page |
| GET    | `/api/portal/subscriptions` | Customer | The customer's own subscriptions. `?page`, `?page_size` | `200` page |
| GET    | `/api/portal/invoices` | Customer | The customer's own invoices, without drafts. `?page`, `?page_size` | `200` page |

A page looks like `{"items": [...], "total": 42, "page": 1, "page_size": 20}`. `page_size` is at most 100. Money values are strings, such as `"1560.00"`, so that no precision is lost. Dates are `YYYY-MM-DD`, and statuses are lower case.

## Catalog

```json
{ "name": "GST 18%", "rate": "18.00" }
```

```json
{
  "name": "Hosting",
  "sales_price": "1000.00",
  "cost_price": "0.00",
  "product_type": "service",
  "description": "Optional",
  "variants": [{ "attribute": "Brand", "value": "Odoo", "extra_price": "560.00" }]
}
```

```json
{
  "name": "Monthly",
  "price": "0.00",
  "billing_period": "monthly",
  "billing_interval": 1,
  "min_quantity": 1,
  "valid_from": "2026-01-01",
  "valid_to": null,
  "is_auto_close": false,
  "is_closable": true,
  "is_pausable": false,
  "is_renewable": false
}
```

```json
{
  "code": "SAVE10",
  "name": "Save 10",
  "discount_type": "percent",
  "scope": "subscription",
  "value": "10.00",
  "min_purchase": "0.00",
  "min_quantity": 1,
  "valid_from": null,
  "valid_to": null,
  "usage_limit": 5,
  "product_ids": []
}
```

`billing_period` is `daily`, `weekly`, `monthly` or `yearly`. `discount_type` is `percent` or `fixed`. `scope` is `subscription` or `product`, and a `product` discount needs `product_ids`. An empty `usage_limit` means unlimited. A name or code already in use returns `409 name_taken`. Items can be created, listed and deactivated, but not edited. To change one, deactivate it and create a replacement. Existing subscriptions keep the prices they were created with.

## Reports

`GET /api/reports/summary`:

```json
{ "active_subscriptions": 4, "mrr": "1624.58", "revenue_collected": "690.00", "outstanding": "420.00", "overdue_count": 3 }
```

`GET /api/reports/revenue` returns a list: `[{ "period": "2025-01-01", "invoiced": "500.00", "collected": "400.00" }]`. `period` is the first day of the month. `invoiced` counts confirmed and paid invoices only, so drafts and cancelled invoices are left out.

Each `GET /api/reports/overdue` item is `invoice_id`, `number`, `customer` (the name), `due_date`, `balance` and `days_overdue`.

## Customer portal

Each `GET /api/portal/subscriptions` item is `subscription_id`, `number`, `status`, `plan_name`, `billing_period`, `price`, `start_date`, `expires_on` and `next_billing_date`.

Each `GET /api/portal/invoices` item is `invoice_id`, `number`, `status`, `total`, `amount_paid`, `balance` and `due_date`.

## Allowed actions

A single subscription or invoice includes `allowed_actions`, the actions this user can take now. Show buttons only for these. Lists leave it out, and customers always get an empty list.

- **Subscriptions:** the state machine action names below, such as `send-quotation`.
- **Invoices:** `confirm`, `cancel`, `send`, and `pay` for recording a payment.

## Quotation templates

```json
{
  "name": "Standard",
  "plan_id": 1,
  "validity_days": 30,
  "lines": [
    { "product_id": 1, "variant_id": 1, "tax_id": 1, "quantity": 2 }
  ]
}
```

`variant_id` and `tax_id` are optional. A template needs at least one line, and each quantity must meet the plan's `min_quantity`. Line errors are reported by position: `fields.lines["0"].variant_id`.

## Subscriptions

Create with `customer_id` and `template_id`. Optional fields are `start_date`, `expires_on`, `discount_id` and `notes`. Customers can read `notes`, so do not put internal comments there.

### State machine

| Action (`POST .../{action}`) | From | To | Also needs | Effect |
| ---------------------------- | ---- | -- | ---------- | ------ |
| `send-quotation` | `draft` | `quotation` | | Restarts the validity period from today |
| `confirm` | `quotation` | `confirmed` | Quotation not expired | |
| `activate` | `confirmed` | `active` | Not past `expires_on` | Sets `start_date` if empty, and `next_billing_date` |
| `pause` | `active` | `paused` | Plan `is_pausable` | |
| `resume` | `paused` | `active` | | Moves `next_billing_date` forward, so paused time is not billed |
| `renew` | `active` | `active` | Plan `is_renewable`, and an `expires_on` | Extends `expires_on` by one billing period |
| `close` | `active`, `paused` | `closed` | Plan `is_closable` | Sets `closed_at` |

Any other move returns `409 invalid_transition` and changes nothing.

## Billing

`POST /api/billing/run` returns a summary:

```json
{ "invoices_created": 2, "duplicates_skipped": 0, "subscriptions_closed": 0, "failures": 0 }
```

- It creates draft invoices for active subscriptions with `next_billing_date` on or before today. A subscription behind by several periods gets one invoice for each.
- Running it again never bills a period twice.
- Periods starting after `expires_on` are not billed. Once `expires_on` has passed, a plan with `is_auto_close` closes the subscription. Otherwise it stays active, unbilled, until it is renewed or closed.
- A discount is applied per invoice, and each discounted invoice uses one of its `usage_limit`. When none are left, or the discount is no longer eligible, the invoice is full price.

## Invoices

| Action | From | To | Notes |
| ------ | ---- | -- | ----- |
| `confirm` | `draft` | `confirmed` | A zero-total invoice goes straight to `paid` |
| `cancel` | `draft`, `confirmed` | `cancelled` | Refused with `invoice_has_payments` once any payment exists |
| A payment | `confirmed` | `paid` | When the full total has been paid |

Any other move returns `409 invalid_transition`. A cancelled invoice keeps its billing period, so that period cannot be billed again.

`is_overdue` is computed when you read the invoice: it is true for a `confirmed` invoice past its `due_date`. It is never a status, so filter with `?overdue=true`.

`customer_snapshot` holds the customer's details as they were when the invoice was created. Display it rather than the current customer record.

## Payments

```json
{ "method": "card", "amount": "250.00", "payment_date": "2026-10-31", "note": "Optional" }
```

`method` is `cash`, `card`, `bank_transfer`, `upi` or `other`. `amount` must be above zero with at most two decimal places. `payment_date` defaults to today and cannot be in the future. Payments are only accepted on `confirmed` invoices (`409 invoice_not_payable`), and cannot exceed the balance due (`409 overpayment`).

### Request bodies

| Endpoint | Fields |
| -------- | ------ |
| `POST /api/auth/register` | `email`, `password`, `full_name` |
| `POST /api/auth/login` | `email`, `password` |
| `POST /api/auth/forgot-password` | `email` |
| `POST /api/auth/reset-password` | `token`, `password` |
| `POST /api/staff` | `email`, `password`, `full_name`, `staff_function` (`sales_rep`, `finance_lead` or `support`) |

### User object

```json
{
  "id": 1,
  "email": "ana@example.com",
  "full_name": "Ana",
  "role": "customer",
  "staff_function": null
}
```

`role` is `admin`, `staff` or `customer`. `staff_function` is only set for staff.

### Password rule

Longer than 8 characters (at most 128), with an uppercase letter, a lowercase letter and a special character. A violation returns `422` with the reasons in `fields.password`.

## Authentication

Login sets the session in cookies. The access token cookie is httpOnly, so JavaScript cannot read it. Use `GET /api/auth/me` to find out who is logged in.

- **Send cookies:** use `credentials: "include"` with `fetch`, or `withCredentials: true` with Axios.
- **CSRF:** on POST, PUT, PATCH and DELETE to a protected endpoint, send an `X-CSRF-TOKEN` header holding the value of the readable `csrf_access_token` cookie. Without it the request returns `401`.
- **Same origin:** the API has no CORS support, so in development proxy `/api` through the frontend dev server (for example with Vite's `server.proxy`).
- **Reset links:** the email links to `{FRONTEND_URL}/reset-password?token=...`. That page should post the token and new password to `/api/auth/reset-password`.

Rate limits per IP address: login and reset-password 5 per minute, forgot-password 5 per 15 minutes, register 10 per minute.

## Error format

Every error response uses this shape:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The submitted data is invalid.",
    "fields": {
      "email": ["Not a valid email address."]
    }
  }
}
```

| Key       | Type   | Description                                                        |
| --------- | ------ | ------------------------------------------------------------------ |
| `code`    | string | Stable, machine-readable identifier. Use this in client logic.     |
| `message` | string | Human-readable description.                                        |
| `fields`  | object | Per-field validation messages. An empty object for other errors.   |

### Common codes

| Status | Code                                                                       | Meaning                                  |
| ------ | -------------------------------------------------------------------------- | ---------------------------------------- |
| 400    | `bad_request`, `invalid_reset_token`                                       | The request could not be processed       |
| 401    | `unauthorized`, `invalid_credentials`, `invalid_token`, `token_expired`, `token_revoked`, `fresh_token_required` | Authentication is missing or not valid |
| 403    | `forbidden`                                                                | Authenticated, but not allowed           |
| 404    | `not_found`                                                                | The resource or route does not exist     |
| 405    | `method_not_allowed`                                                       | The route does not support the method    |
| 413    | `request_entity_too_large`                                                 | The request body is over 1 MB            |
| 409    | `conflict`, `email_taken`, `name_taken`, `invalid_transition`, `action_not_allowed_by_plan`, `quotation_expired`, `subscription_expired`, `no_expiry_date`, `plan_unavailable`, `catalog_item_inactive`, `below_plan_minimum`, `invoice_has_payments`, `invoice_not_sendable`, `invoice_not_payable`, `overpayment` | Conflicts with the current state |
| 422    | `validation_error`                                                         | The submitted data failed validation     |
| 429    | `too_many_requests`                                                        | Rate limit exceeded                      |
| 500    | `internal_server_error`                                                    | Unexpected server error                  |

## Request IDs

Every response has an `X-Request-ID` header, and the same id appears in the server logs.
A client can supply its own id with that header, using up to 64 letters, digits, `.`, `_` or `-`.
Any other value is replaced with a generated id.
