"""Liveness and readiness endpoints."""
from flask import Blueprint, jsonify

from app.services import health_service

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@health_bp.get("/health/ready")
def ready():
    """For a load balancer or uptime check: also proves the database answers."""
    if health_service.database_is_reachable():
        return jsonify({"status": "ok"})
    return jsonify({"status": "unavailable"}), 503
