"""Serves the built frontend, so that one server handles the whole app."""
from pathlib import Path

from flask import Flask, abort, send_from_directory

from app.core.errors import NotFound

_ONE_YEAR = 60 * 60 * 24 * 365


def register_frontend(app: Flask) -> None:
    dist = app.config.get("FRONTEND_DIST")
    if not dist or not (Path(dist) / "index.html").is_file():
        return
    dist = Path(dist).resolve()

    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def frontend(path):
        if path == "api" or path.startswith("api/"):
            raise NotFound()
        # send_from_directory refuses anything outside dist. Vite puts a content
        # hash in asset names, so a changed file always has a new name.
        if path and (dist / path).is_file():
            max_age = _ONE_YEAR if path.startswith("assets/") else 3600
            return send_from_directory(dist, path, max_age=max_age)
        if "." in path.rsplit("/", 1)[-1]:
            abort(404)
        # Any other path is a route inside the React app. No caching, so that a
        # new release is picked up on the next page load.
        response = send_from_directory(dist, "index.html", max_age=0)
        response.headers["Cache-Control"] = "no-cache"
        return response
