from pydantic import ValidationError

from buma.schemas.normalized_event import NormalizedEvent


def sample_payload() -> dict:
    return {
        "schema_version": "1.0",
        "event_id": "9d3d6c20-2a71-11ef-9a3b-acde48001122",
        "delivery_id": "9d3d6c20-2a71-11ef-9a3b-acde48001122",
        "event_name": "issues",
        "action": "opened",
        "received_at": "2026-02-23T17:25:00Z",
        "installation_id": 12345678,
        "repo": {
            "id": 123456789,
            "full_name": "acme-org/payments-service",
            "private": False,
        },
        "issue": {
            "number": 42,
            "id": 987654321,
            "node_id": "I_kwDOExample123",
            "url": "https://api.github.com/repos/acme-org/payments-service/issues/42",
            "html_url": "https://github.com/acme-org/payments-service/issues/42",
            "title": "Checkout fails on Safari",
            "body": "Steps to reproduce: ...",
            "labels": ["bug", "p1", "frontend"],
            "author_login": "octocat",
            "created_at": "2026-02-23T17:20:00Z",
            "updated_at": "2026-02-23T17:21:00Z",
        },
        "sender_login": "octocat",
        "trace_id": "trace-01J2Z8Y6Z3J8Q9K7V5H2K1M0N9",
    }


def test_normalized_event_accepts_valid_payload():
    evt = NormalizedEvent.model_validate(sample_payload())

    assert evt.schema_version == "1.0"
    assert evt.event_name == "issues"
    assert evt.action == "opened"
    assert evt.repo.full_name == "acme-org/payments-service"
    assert evt.issue.number == 42
    assert "bug" in evt.issue.labels


def test_normalized_event_rejects_unknown_fields_when_forbid_enabled():
    payload = sample_payload()
    payload["issue"]["unexpected_field"] = "nope"

    try:
        NormalizedEvent.model_validate(payload)
        assert False, "Expected ValidationError due to unknown field"
    except ValidationError:
        assert True
