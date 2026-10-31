"""Production server. `flask run` is for development only.

    python serve.py

HOST and PORT are optional. Keep HOST on 127.0.0.1 behind a reverse proxy.
"""
import os

from waitress import serve

from wsgi import app

if __name__ == "__main__":
    serve(
        app,
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        threads=int(os.getenv("THREADS", "8")),
    )
