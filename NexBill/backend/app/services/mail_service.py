"""Outgoing email, using only the standard library."""
import logging
import smtplib
import threading
import uuid
from email.message import EmailMessage
from pathlib import Path

from flask import current_app

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    """Send in the background, so a caller's response time reveals nothing.

    Without this, forgot-password would answer visibly slower for a real account.
    """
    config = current_app.config
    message = EmailMessage()
    message["From"] = config["MAIL_FROM"]
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    settings = {
        "host": config["SMTP_HOST"],
        "port": config["SMTP_PORT"],
        "username": config["SMTP_USERNAME"],
        "password": config["SMTP_PASSWORD"],
        "outbox_dir": config["MAIL_OUTBOX_DIR"],
    }
    threading.Thread(target=_deliver, args=(message, settings), daemon=True).start()


def _deliver(message: EmailMessage, settings: dict) -> None:
    # Failures log the error type only: message contents can hold reset links.
    try:
        if settings["host"]:
            _send_over_smtp(message, settings)
        elif settings["outbox_dir"]:
            _write_to_outbox(message, settings["outbox_dir"])
        else:
            logger.warning("email dropped: no SMTP_HOST or outbox configured")
    except (OSError, smtplib.SMTPException) as error:
        logger.error("email delivery failed: %s", type(error).__name__)


def _send_over_smtp(message: EmailMessage, settings: dict) -> None:
    with smtplib.SMTP(settings["host"], settings["port"], timeout=10) as smtp:
        if settings["username"]:
            smtp.starttls()
            smtp.login(settings["username"], settings["password"])
        smtp.send_message(message)


def _write_to_outbox(message: EmailMessage, outbox_dir: str) -> None:
    # Plain text rather than raw .eml, where encoding would wrap long lines and
    # corrupt any link a developer copies out of the file.
    directory = Path(outbox_dir)
    directory.mkdir(parents=True, exist_ok=True)
    text = (
        f"To: {message['To']}\nSubject: {message['Subject']}\n\n"
        f"{message.get_content()}"
    )
    (directory / f"{uuid.uuid4().hex}.txt").write_text(text, encoding="utf-8")
