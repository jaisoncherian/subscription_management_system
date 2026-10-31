"""Flask CLI commands."""
import click
from flask import Flask, current_app
from flask.cli import with_appcontext

from app.core.errors import AppError
from app.services import user_service


def register_commands(app: Flask) -> None:
    app.cli.add_command(create_admin)


@click.command("create-admin")
@with_appcontext
def create_admin():
    """Create the admin from ADMIN_EMAIL and ADMIN_PASSWORD. Safe to run twice."""
    email = current_app.config["ADMIN_EMAIL"]
    password = current_app.config["ADMIN_PASSWORD"]
    if not email or not password:
        raise click.ClickException("Set ADMIN_EMAIL and ADMIN_PASSWORD in .env.")

    try:
        user, created = user_service.ensure_admin(email, password)
    except AppError as error:
        details = "; ".join(
            message for messages in error.fields.values() for message in messages
        )
        raise click.ClickException(f"{error.message} {details}".strip()) from None

    if created:
        click.echo(f"Admin created: {user.email}")
    else:
        click.echo(f"Admin already exists: {user.email}. Password not changed.")
