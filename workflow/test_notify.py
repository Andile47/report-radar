import smtplib
from email import policy
from email.parser import BytesParser

import pytest

from governance import logger
from workflow import notify as notify_mod

RESIDENT = "resident.sipho@example.org"

TICKET = {
    "ticket_id": "TKT000042",
    "received_at": "2026-11-03T08:15:00",
    "description_masked": "Water pipe burst. Call 082 123 4567, ID 9001015009087, thandi@example.com",
    "ward": "Setswetla",
    "resident_contact": "yes",
    "category": "water",
    "urgency": 5,
    "review_required": False,
    "reason": "burst pipe",
    "assigned_team": "Water team",
    "depot": "North depot",
    "sla_hours": 24,
    "due_by": "2026-11-04T08:15:00",
    "status": "awaiting_approval",
    "approval_status": "pending",
}


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(notify_mod, "OUTBOX_DIR", tmp_path / "outbox")
    monkeypatch.setattr(logger, "LOG_FILE", tmp_path / "decisions.csv")
    for name in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"):
        monkeypatch.delenv(name, raising=False)

    def no_smtp(*args, **kwargs):
        raise AssertionError("smtplib.SMTP must not be called without full SMTP settings")

    monkeypatch.setattr(smtplib, "SMTP", no_smtp)
    return tmp_path


def raw(path):
    return path.read_bytes().decode("utf-8", "replace")


def body(path):
    return BytesParser(policy=policy.default).parsebytes(path.read_bytes()).get_content()


def all_outbox_text(tmp_path):
    return "".join(raw(p) for p in (tmp_path / "outbox").glob("*.eml"))


@pytest.mark.parametrize("event", ["received", "assigned", "approval_needed", "overdue"])
def test_each_event_creates_a_readable_email_with_the_ticket_number(event, isolated):
    path = notify_mod.notify(event, TICKET, resident_email=RESIDENT, now="2026-11-04T20:15:00")
    assert path.exists() and path.suffix == ".eml"
    assert "TKT000042" in raw(path)
    assert body(path).strip()


def test_personal_details_are_masked_in_team_and_supervisor_emails(isolated):
    team = notify_mod.notify("assigned", TICKET)
    supervisor = notify_mod.notify("approval_needed", TICKET)
    for path in (team, supervisor):
        text = raw(path)
        assert "[PHONE]" in text and "[ID]" in text and "[EMAIL]" in text
        assert "082 123 4567" not in text
        assert "9001015009087" not in text
        assert "thandi@example.com" not in text


def test_resident_address_never_reaches_team_supervisor_outbox_or_log(isolated):
    notify_mod.notify("received", TICKET, resident_email=RESIDENT)
    notify_mod.notify("assigned", TICKET, now="2026-11-03T09:00:00")
    notify_mod.notify("approval_needed", TICKET)
    notify_mod.notify("overdue", TICKET, now="2026-11-04T20:15:00")
    assert RESIDENT not in all_outbox_text(isolated)
    log_text = (isolated / "decisions.csv").read_text(encoding="utf-8")
    assert RESIDENT not in log_text
    assert "notifications" in log_text and "sent to: resident" in log_text


def test_no_resident_email_means_no_received_email(isolated):
    assert notify_mod.notify("received", TICKET) is None
    assert notify_mod.notify("received", TICKET, resident_email="") is None
    assert not (isolated / "outbox").exists() or not list((isolated / "outbox").glob("*.eml"))


def test_overdue_email_says_how_many_hours(isolated):
    path = notify_mod.notify("overdue", TICKET, now="2026-11-04T20:15:00")  # due 08:15, now 20:15
    assert "12 hours" in body(path)


def test_approval_email_explains_why(isolated):
    urgent = notify_mod.notify("approval_needed", TICKET)
    assert "urgent" in body(urgent)
    unclear = dict(TICKET, urgency=2, review_required=True, ticket_id="TKT000043")
    assert "not sure" in body(notify_mod.notify("approval_needed", unclear))


def test_unknown_event_is_rejected(isolated):
    with pytest.raises(ValueError):
        notify_mod.notify("birthday", TICKET)


def test_only_part_of_the_smtp_settings_means_nothing_is_sent(isolated, monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.org")  # no user or password
    assert notify_mod.notify("assigned", TICKET).exists()  # saved, and smtplib untouched


def test_full_smtp_settings_send_for_real_but_the_saved_copy_hides_the_resident(isolated, monkeypatch):
    sent = []

    class FakeSMTP:
        def __init__(self, host, port, timeout=None):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self):
            pass

        def login(self, user, password):
            pass

        def send_message(self, message):
            sent.append(message["To"])

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.org")
    monkeypatch.setenv("SMTP_USER", "user")
    monkeypatch.setenv("SMTP_PASSWORD", "not-a-real-password")
    path = notify_mod.notify("received", TICKET, resident_email=RESIDENT)
    assert sent == [RESIDENT]
    assert RESIDENT not in raw(path)


def test_a_failed_send_does_not_lose_the_email_or_raise(isolated, monkeypatch):
    def broken(*args, **kwargs):
        raise OSError("network down")

    monkeypatch.setattr(smtplib, "SMTP", broken)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.org")
    monkeypatch.setenv("SMTP_USER", "user")
    monkeypatch.setenv("SMTP_PASSWORD", "not-a-real-password")
    assert notify_mod.notify("assigned", TICKET).exists()
