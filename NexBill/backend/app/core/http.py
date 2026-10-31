"""Security headers on every response."""
from flask import Flask

# Inline styles are allowed because the app sets bar heights and the printable
# invoice carries its own stylesheet. Scripts only ever come from this origin.
def content_security_policy(script_source: str = "'self'") -> str:
    return (
        f"default-src 'self'; script-src {script_source}; "
        "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
        "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
    )


def register_security_headers(app: Flask) -> None:
    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("Content-Security-Policy", content_security_policy())
        if app.config["IS_PRODUCTION"] and app.config["JWT_COOKIE_SECURE"]:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response
