"""WSGI entry point. `flask run` finds this file automatically."""
from app import create_app

app = create_app()
