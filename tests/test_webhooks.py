"""Tests for webhook signature verification and event dedup."""

from lenrose.server.routes.webhooks import verify_signature


def test_verify_signature_valid():
    import hashlib
    import hmac

    secret = "s3cr3t"
    body = b'{"type":"container-child-created"}'
    header = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_signature(body, secret, header) is True


def test_verify_signature_invalid():
    assert verify_signature(b"body", "secret", "sha256=deadbeef") is False
    assert verify_signature(b"body", "secret", None) is False


def test_record_seen_event_dedup(tmp_path):
    from lenrose.state import db

    db_path = str(tmp_path / "state.db")
    db.init_db(db_path)
    assert db.record_seen_event("evt-1") is True
    assert db.record_seen_event("evt-1") is False
    assert db.record_seen_event("evt-2") is True
