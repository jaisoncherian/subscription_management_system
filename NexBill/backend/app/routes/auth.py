"""Authentication endpoints."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    get_current_user,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
)

from app.extensions import limiter
from app.schemas.auth import (
    ForgotPasswordSchema,
    LoginSchema,
    RegisterSchema,
    ResetPasswordSchema,
    UserSchema,
)
from app.services import auth_service

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

FORGOT_PASSWORD_REPLY = "If that email has an account, a reset link has been sent."


@auth_bp.post("/register")
@limiter.limit("10 per minute")
def register():
    data = RegisterSchema().load(request.get_json())
    user = auth_service.register_customer(**data)
    return jsonify(UserSchema().dump(user)), 201


@auth_bp.post("/login")
@limiter.limit("5 per minute")
def login():
    data = LoginSchema().load(request.get_json())
    user, access_token = auth_service.login(**data)
    response = jsonify(UserSchema().dump(user))
    set_access_cookies(response, access_token)
    return response


@auth_bp.post("/logout")
def logout():
    response = jsonify({"message": "Logged out."})
    unset_jwt_cookies(response)
    return response


@auth_bp.get("/me")
@jwt_required()
def me():
    return jsonify(UserSchema().dump(get_current_user()))


@auth_bp.post("/forgot-password")
@limiter.limit("5 per 15 minutes")
def forgot_password():
    data = ForgotPasswordSchema().load(request.get_json())
    auth_service.request_password_reset(**data)
    return jsonify({"message": FORGOT_PASSWORD_REPLY})


@auth_bp.post("/reset-password")
@limiter.limit("5 per minute")
def reset_password():
    data = ResetPasswordSchema().load(request.get_json())
    auth_service.reset_password(data["token"], data["password"])
    return jsonify({"message": "Your password has been reset."})
