"""Application errors and the handlers that render them.

Every error response has the shape:
    {"error": {"code": str, "message": str, "fields": dict}}
"""
from flask import Flask, current_app, jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException

from app.extensions import jwt


class AppError(Exception):
    """Base class for errors raised deliberately by application code."""

    status_code = 400
    code = "bad_request"
    message = "The request could not be processed."

    def __init__(self, message=None, *, code=None, status_code=None, fields=None):
        super().__init__(message or self.message)
        self.message = message or self.message
        self.code = code or self.code
        self.status_code = status_code or self.status_code
        self.fields = fields or {}


class NotFound(AppError):
    status_code = 404
    code = "not_found"
    message = "Resource not found."


class Forbidden(AppError):
    status_code = 403
    code = "forbidden"
    message = "You do not have permission to perform this action."


class Conflict(AppError):
    status_code = 409
    code = "conflict"
    message = "The request conflicts with the current state of the resource."


def error_response(code, message, status_code, fields=None):
    body = {"error": {"code": code, "message": message, "fields": fields or {}}}
    return jsonify(body), status_code


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return error_response(err.code, err.message, err.status_code, err.fields)

    @app.errorhandler(ValidationError)
    def handle_validation_error(err):
        return error_response(
            "validation_error",
            "The submitted data is invalid.",
            422,
            err.normalized_messages(),
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        # Covers routing errors, malformed bodies and Flask-Limiter's 429.
        code = err.name.lower().replace(" ", "_")
        response, status_code = error_response(code, err.description, err.code)
        # Keep headers the status relies on, such as Allow on a 405.
        for name, value in err.get_headers():
            if name.lower() != "content-type":
                response.headers[name] = value
        return response, status_code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        current_app.logger.exception("Unhandled exception")
        return error_response(
            "internal_server_error", "An unexpected error occurred.", 500
        )

    _register_jwt_error_handlers()


def _register_jwt_error_handlers() -> None:
    """Replace Flask-JWT-Extended's default {"msg": ...} responses."""

    @jwt.unauthorized_loader
    def missing_token(reason):
        return error_response("unauthorized", reason, 401)

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return error_response("invalid_token", reason, 401)

    @jwt.expired_token_loader
    def expired_token(_header, _payload):
        return error_response("token_expired", "The token has expired.", 401)

    @jwt.revoked_token_loader
    def revoked_token(_header, _payload):
        return error_response("token_revoked", "The token has been revoked.", 401)

    @jwt.needs_fresh_token_loader
    def stale_token(_header, _payload):
        return error_response(
            "fresh_token_required", "A fresh token is required.", 401
        )
