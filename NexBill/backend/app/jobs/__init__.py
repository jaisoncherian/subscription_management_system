"""Flask CLI commands."""
import click
from flask import Flask, current_app
from flask.cli import with_appcontext

from app.core.errors import AppError
from app.jobs import seed_data
from app.services import billing_service, user_service


def register_commands(app: Flask) -> None:
    app.cli.add_command(create_admin)
    app.cli.add_command(run_billing)
    app.cli.add_command(seed_demo)


@click.command("run-billing")
@with_appcontext
def run_billing():
    """Invoice every subscription that is due. Safe to run more than once."""
    summary = billing_service.run_billing()
    click.echo(
        f"Invoices created: {summary['invoices_created']}, "
        f"duplicates skipped: {summary['duplicates_skipped']}, "
        f"subscriptions closed: {summary['subscriptions_closed']}, "
        f"failures: {summary['failures']}"
    )
    if summary["failures"]:
        raise click.ClickException("Some subscriptions failed. See the logs for details.")


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


@click.command("seed-demo")
@with_appcontext
def seed_demo():
    """Fill an empty database with demo data. Does nothing if it has already run."""
    config = current_app.config
    if config["IS_PRODUCTION"]:
        raise click.ClickException("seed-demo refuses to run in production.")
    missing = [
        name for name in ("ADMIN_EMAIL", "ADMIN_PASSWORD", "DEMO_PASSWORD") if not config[name]
    ]
    if missing:
        raise click.ClickException(f"Set {', '.join(missing)} in .env.")

    summary = seed_data.seed_demo(config["ADMIN_EMAIL"], config["ADMIN_PASSWORD"], config["DEMO_PASSWORD"])
    if summary is None:
        click.echo("Demo data is already there. Nothing changed.")
        return
    click.echo(
        f"Created {summary['subscriptions']} subscriptions, {summary['invoices']} invoices "
        f"and {summary['payments']} payments."
    )
    click.echo(f"Staff login: {summary['staff_email']}")
    click.echo(f"Customer login: {summary['customer_email']}")
    click.echo("Their password is DEMO_PASSWORD in .env.")
