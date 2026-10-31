# NexBill API

Base path: `/api`

## Endpoints

| Method | Path          | Auth | Description  | Success response     |
| ------ | ------------- | ---- | ------------ | -------------------- |
| GET    | `/api/health` | None | Health check | `200 {"status":"ok"}` |
| POST   | `/api/auth/register` | None | Public signup. Always creates a customer | `201` user |
| POST   | `/api/auth/login` | None | Log in and set the session cookies | `200` user |
| POST   | `/api/auth/logout` | None | Clear the session cookies | `200 {"message"}` |
| GET    | `/api/auth/me` | Any logged-in user | The current user | `200` user |
| POST   | `/api/auth/forgot-password` | None | Email a reset link. Same reply for any email | `200 {"message"}` |
| POST   | `/api/auth/reset-password` | None | Set a new password with a reset token | `200 {"message"}` |
| POST   | `/api/staff` | Admin | Create a staff account | `201` user |
| POST   | `/api/quotation-templates` | Admin | Create a template | `201` template |
| GET    | `/api/quotation-templates` | Admin, staff | List templates. `?page`, `?per_page`, `?include_inactive=true` | `200` page |
| GET    | `/api/quotation-templates/{id}` | Admin, staff | One template | `200` template |
| PUT    | `/api/quotation-templates/{id}` | Admin | Replace a template. Existing subscriptions do not change | `200` template |
| DELETE | `/api/quotation-templates/{id}` | Admin | Deactivate a template. It is kept, not deleted | `200` template |
| POST   | `/api/subscriptions` | Admin, staff | Create a draft subscription from a template | `201` subscription |
| GET    | `/api/subscriptions` | Any logged-in user | List subscriptions. Customers get only their own. `?status`, `?page`, `?per_page` | `200` page |
| GET    | `/api/subscriptions/{id}` | Any logged-in user | One subscription. Another customer's returns `404` | `200` subscription |
| POST   | `/api/subscriptions/{id}/{action}` | Admin, staff | Change state. No request body | `200` subscription |
| POST   | `/api/billing/run` | Admin | Invoice everything that is due. Same as `flask run-billing` | `200` summary |
| GET    | `/api/invoices` | Any logged-in user | List invoices. Customers get only their own, without drafts. `?status`, `?overdue=true`, `?customer_id`, `?page`, `?per_page` | `200` page |
| GET    | `/api/invoices/{id}` | Any logged-in user | One invoice. Another customer's returns `404` | `200` invoice |
| GET    | `/api/invoices/{id}/print` | Any logged-in user | Printable HTML page. Use the browser to print or save as PDF | `200` HTML |
| POST   | `/api/invoices/{id}/confirm` | Admin, staff | Draft to confirmed. No request body | `200` invoice |
| POST   | `/api/invoices/{id}/cancel` | Admin, staff | Cancel before paid. No request body | `200` invoice |
| POST   | `/api/invoices/{id}/send` | Admin, staff | Email a confirmed or paid invoice. No request body | `200` invoice |
| GET    | `/api/invoices/{id}/payments` | Any logged-in user | Payments on an invoice | `200` list |
| POST   | `/api/invoices/{id}/payments` | Admin, staff | Record a payment | `201` payment |

More endpoints will be listed here as features are built.

A page looks like `{"items": [...], "total": 42, "page": 1, "per_page": 20}`. `per_page` is at most 100. Money values are strings, such as `"1560.00"`, so that no precision is lost.

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
| 409    | `conflict`, `email_taken`, `name_taken`, `invalid_transition`, `action_not_allowed_by_plan`, `quotation_expired`, `subscription_expired`, `no_expiry_date`, `plan_unavailable`, `catalog_item_inactive`, `below_plan_minimum`, `invoice_has_payments`, `invoice_not_sendable`, `invoice_not_payable`, `overpayment` | Conflicts with the current state |
| 422    | `validation_error`                                                         | The submitted data failed validation     |
| 429    | `too_many_requests`                                                        | Rate limit exceeded                      |
| 500    | `internal_server_error`                                                    | Unexpected server error                  |

## Request IDs

Every response has an `X-Request-ID` header, and the same id appears in the server logs.
A client can supply its own id with that header, using up to 64 letters, digits, `.`, `_` or `-`.
Any other value is replaced with a generated id.
