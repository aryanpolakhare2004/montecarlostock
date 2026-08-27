import pytest

from mcstock.web import notifications


@pytest.fixture(autouse=True)
def _clear_notification_env(monkeypatch):
    for key in (
        "MCSTOCK_ALERT_WEBHOOK_URL", "MCSTOCK_ALERT_EMAIL_TO", "MCSTOCK_SMTP_HOST",
        "MCSTOCK_SMTP_PORT", "MCSTOCK_SMTP_USER", "MCSTOCK_SMTP_PASSWORD", "MCSTOCK_ALERT_EMAIL_FROM",
    ):
        monkeypatch.delenv(key, raising=False)


def _sample_alert():
    return {"ticker": "AAPL", "metric": "price", "operator": "above", "threshold": 150.0}


# ---- webhook ----

def test_webhook_not_sent_when_unset(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("requests.post should not be called")

    monkeypatch.setattr(notifications.requests, "post", boom)
    notifications._send_webhook(_sample_alert())  # must not raise


def test_webhook_sent_when_configured(monkeypatch):
    monkeypatch.setenv("MCSTOCK_ALERT_WEBHOOK_URL", "https://example.com/hook")
    calls = []
    monkeypatch.setattr(notifications.requests, "post", lambda url, json, timeout: calls.append((url, json, timeout)))

    notifications._send_webhook(_sample_alert())

    assert len(calls) == 1
    url, payload, timeout = calls[0]
    assert url == "https://example.com/hook"
    assert payload["alert"]["ticker"] == "AAPL"
    assert "AAPL" in payload["text"]
    assert timeout == 10


def test_webhook_failure_is_swallowed(monkeypatch):
    monkeypatch.setenv("MCSTOCK_ALERT_WEBHOOK_URL", "https://example.com/hook")

    def boom(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(notifications.requests, "post", boom)
    notifications._send_webhook(_sample_alert())  # must not raise


# ---- email ----

class _FakeSMTP:
    sent_messages: list = []

    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def starttls(self):
        pass

    def login(self, user, password):
        self.login_args = (user, password)

    def send_message(self, message):
        _FakeSMTP.sent_messages.append(message)


def test_email_not_sent_when_unset(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("smtplib.SMTP should not be called")

    monkeypatch.setattr(notifications.smtplib, "SMTP", boom)
    notifications._send_email(_sample_alert())  # must not raise


def test_email_sent_when_configured(monkeypatch):
    monkeypatch.setenv("MCSTOCK_ALERT_EMAIL_TO", "me@example.com")
    monkeypatch.setenv("MCSTOCK_SMTP_HOST", "smtp.example.com")
    _FakeSMTP.sent_messages = []
    monkeypatch.setattr(notifications.smtplib, "SMTP", _FakeSMTP)

    notifications._send_email(_sample_alert())

    assert len(_FakeSMTP.sent_messages) == 1
    message = _FakeSMTP.sent_messages[0]
    assert message["To"] == "me@example.com"
    assert "AAPL" in message["Subject"]


def test_email_failure_is_swallowed(monkeypatch):
    monkeypatch.setenv("MCSTOCK_ALERT_EMAIL_TO", "me@example.com")
    monkeypatch.setenv("MCSTOCK_SMTP_HOST", "smtp.example.com")

    def boom(*args, **kwargs):
        raise RuntimeError("smtp down")

    monkeypatch.setattr(notifications.smtplib, "SMTP", boom)
    notifications._send_email(_sample_alert())  # must not raise


# ---- dispatcher ----

def test_notify_alert_triggered_calls_both_channels(monkeypatch):
    calls = []
    monkeypatch.setattr(notifications, "_send_webhook", lambda alert: calls.append("webhook"))
    monkeypatch.setattr(notifications, "_send_email", lambda alert: calls.append("email"))

    notifications.notify_alert_triggered(_sample_alert())

    assert calls == ["webhook", "email"]
