from __future__ import annotations

import hashlib
import hmac

from buma.core.security import verify_github_signature

SECRET = "test-secret"


def _sign(payload: bytes, secret: str = SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256).hexdigest()


def test_valid_signature_returns_true():
    payload = b'{"action":"opened"}'
    assert verify_github_signature(payload, _sign(payload), SECRET) is True


def test_wrong_secret_returns_false():
    payload = b'{"action":"opened"}'
    sig = _sign(payload, secret="wrong-secret")
    assert verify_github_signature(payload, sig, SECRET) is False


def test_missing_sha256_prefix_returns_false():
    assert verify_github_signature(b"payload", "badhash", SECRET) is False


def test_empty_signature_returns_false():
    assert verify_github_signature(b"payload", "", SECRET) is False


def test_tampered_payload_returns_false():
    original = b'{"action":"opened"}'
    sig = _sign(original)
    assert verify_github_signature(b'{"action":"closed"}', sig, SECRET) is False
