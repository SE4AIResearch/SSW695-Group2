"""
Webhook construction and delivery for the smoke test.

Responsibilities:
  - build_webhook:              generate a delivery_id and construct the payload together
  - build_github_issue_payload: construct a minimal GitHub issues.opened payload
  - sign_webhook_body:          compute the X-Hub-Signature-256 header value
  - send_webhook:               POST the signed payload to the gateway
"""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid

import httpx

from buma.core.config import Settings
from smoke.config import GATEWAY_URL, INSTALLATION_ID, ISSUE_NUMBER, REPO_FULL_NAME, REPO_ID
from smoke.console import fail


def build_webhook() -> tuple[str, dict]:
    """
    Generate a fresh delivery_id and build the corresponding webhook payload.
    Returns (delivery_id, payload) so callers never need to construct an ID separately.
    """
    delivery_id = str(uuid.uuid4())
    payload = build_github_issue_payload()
    return delivery_id, payload


def build_github_issue_payload() -> dict:
    """
    Return a minimal GitHub issues.opened webhook payload.
    The issue title and body contain bug-signal keywords so the
    triage engine classifies it as category=bug, priority=P1.
    """
    return {
        "action": "opened",
        "installation": {"id": INSTALLATION_ID},
        "repository": {
            "id": REPO_ID,
            "full_name": REPO_FULL_NAME,
            "name": REPO_FULL_NAME.split("/")[1],
            "private": False,
        },
        "issue": {
            "id": 9900000042,
            "node_id": "I_smoke_node_42",
            "number": ISSUE_NUMBER,
            "title": "Login button crashes — exception thrown on mobile Safari",
            "body": (
                "Steps to reproduce:\n"
                "1. Open on mobile Safari\n"
                "2. Tap Login\n\n"
                "Actual: traceback shown, app freezes\n"
                "Expected: user is logged in"
            ),
            "html_url": f"https://github.com/{REPO_FULL_NAME}/issues/{ISSUE_NUMBER}",
            "url": f"https://api.github.com/repos/{REPO_FULL_NAME}/issues/{ISSUE_NUMBER}",
            "labels": [],
            "user": {"login": "octocat"},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        },
        "sender": {"login": "octocat"},
    }


def sign_webhook_body(body: bytes, secret: str) -> str:
    """Return the X-Hub-Signature-256 header value for the given body and secret."""
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def send_webhook(delivery_id: str, payload: dict, settings: Settings) -> dict:
    """
    POST a signed webhook to the running gateway.
    Returns the parsed JSON response body.
    Calls fail() if the gateway does not return HTTP 202.
    """
    raw_body = json.dumps(payload).encode()
    signature = sign_webhook_body(raw_body, settings.github_webhook_secret)

    with httpx.Client() as client:
        response = client.post(
            f"{GATEWAY_URL}/webhook/github",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-GitHub-Event": "issues",
                "X-GitHub-Delivery": delivery_id,
                "X-Hub-Signature-256": signature,
            },
        )

    if response.status_code != 202:
        fail(f"Gateway returned HTTP {response.status_code}: {response.text}")

    return response.json()
