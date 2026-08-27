"""Optional email/webhook delivery when a watchlist alert triggers. Both
channels are opt-in via environment variables -- with neither set, alerts
still show up in-app (toast + triggered_at) and this module is a no-op.
"""
from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

import requests

logger = logging.getLogger(__name__)


def _format_message(alert: dict) -> str:
    comparator = ">" if alert["operator"] == "above" else "<"
    return f"{alert['ticker']}: {alert['metric']} {comparator} {alert['threshold']} triggered"


def _send_webhook(alert: dict) -> None:
    url = os.environ.get("MCSTOCK_ALERT_WEBHOOK_URL")
    if not url:
        return
    try:
        requests.post(url, json={"text": _format_message(alert), "alert": alert}, timeout=10)
    except Exception as exc:
        logger.warning("alert webhook delivery failed: %s", exc)


def _send_email(alert: dict) -> None:
    to_addr = os.environ.get("MCSTOCK_ALERT_EMAIL_TO")
    host = os.environ.get("MCSTOCK_SMTP_HOST")
    if not to_addr or not host:
        return

    port = int(os.environ.get("MCSTOCK_SMTP_PORT", "587"))
    user = os.environ.get("MCSTOCK_SMTP_USER")
    password = os.environ.get("MCSTOCK_SMTP_PASSWORD")
    from_addr = os.environ.get("MCSTOCK_ALERT_EMAIL_FROM", user or to_addr)

    message = EmailMessage()
    message["Subject"] = f"mcstock alert: {alert['ticker']}"
    message["From"] = from_addr
    message["To"] = to_addr
    message.set_content(_format_message(alert))

    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            smtp.starttls()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(message)
    except Exception as exc:
        logger.warning("alert email delivery failed: %s", exc)


def notify_alert_triggered(alert: dict) -> None:
    _send_webhook(alert)
    _send_email(alert)
