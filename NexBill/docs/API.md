# NexBill API

Base path: `/api`

## Endpoints

| Method | Path          | Auth | Description  | Success response     |
| ------ | ------------- | ---- | ------------ | -------------------- |
| GET    | `/api/health` | None | Health check | `200 {"status":"ok"}` |

More endpoints will be listed here as features are built.

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
| 400    | `bad_request`                                                              | The request could not be processed       |
| 401    | `unauthorized`, `invalid_token`, `token_expired`, `token_revoked`, `fresh_token_required` | Authentication is missing or not valid |
| 403    | `forbidden`                                                                | Authenticated, but not allowed           |
| 404    | `not_found`                                                                | The resource or route does not exist     |
| 405    | `method_not_allowed`                                                       | The route does not support the method    |
| 409    | `conflict`                                                                 | Conflicts with the current state         |
| 422    | `validation_error`                                                         | The submitted data failed validation     |
| 429    | `too_many_requests`                                                        | Rate limit exceeded                      |
| 500    | `internal_server_error`                                                    | Unexpected server error                  |

## Request IDs

Every response has an `X-Request-ID` header, and the same id appears in the server logs.
A client can supply its own id with that header, using up to 64 letters, digits, `.`, `_` or `-`.
Any other value is replaced with a generated id.
