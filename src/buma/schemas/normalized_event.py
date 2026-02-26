from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# This will chnage only when we make a breaking change to the contract.
SCHEMA_VERSION = "1.0"


class RepoRef(BaseModel):
    """
    Minimal repository identity + privacy flags needed by the triage pipeline.
    """

    model_config = ConfigDict(extra="forbid")
    id: int = Field(
        ...,
        description="GitHub repository numeric ID (stable identifier).",
        examples=[123456789],
    )
    full_name: str = Field(
        ...,
        description='GitHub repository full name in the form "owner/repo".',
        examples=["stevens/buma-service"],
    )
    private: bool = Field(
        ...,
        description="Whether the repository is private (affects access/logging policies).",
        examples=[False],
    )


class IssueRef(BaseModel):
    """
    Minimal issue snapshot fields needed to triage, classify, and assign.
    """

    model_config = ConfigDict(extra="forbid")
    number: int = Field(
        ...,
        description="Issue number within the repository (used for API patch/update).",
        examples=[42],
    )
    id: int = Field(
        ...,
        description="GitHub issue numeric ID (stable identifier).",
        examples=[987654321],
    )
    node_id: str = Field(
        ...,
        description="GitHub GraphQL node ID for the issue (useful for GraphQL integrations).",
        examples=["I_kwDOExample123"],
    )
    url: str = Field(
        ...,
        description="GitHub REST API URL for the issue resource.",
        examples=["https://api.github.com/repos/stevens/buma-service/issues/42"],
    )
    html_url: str = Field(
        ...,
        description="Human-facing GitHub URL for the issue (useful for dashboards/links).",
        examples=["https://github.com/stevens/buma-service/issues/42"],
    )
    title: str = Field(
        ...,
        description="Issue title used in ML features and dashboard summaries.",
        examples=["Checkout fails on Safari"],
    )
    body: str | None = Field(
        default=None,
        description="Issue body text (may be null/empty). Used for NLP/ML features.",
        examples=["Steps to reproduce: ..."],
    )
    labels: list[str] = Field(
        default_factory=list,
        description="List of label *names* (strings only) on the issue at ingestion time.",
        examples=[["bug", "p1", "frontend"]],
    )
    author_login: str = Field(
        ...,
        description="GitHub username (login) of the issue author.",
        examples=["octocat"],
    )
    created_at: datetime = Field(
        ...,
        description="Issue creation timestamp from GitHub (ISO8601 parsed to datetime).",
    )
    updated_at: datetime = Field(
        ...,
        description="Issue last-updated timestamp from GitHub (ISO8601 parsed to datetime).",
    )


class NormalizedEvent(BaseModel):
    """
    Queue boundary contract between:
      - Webhook Gateway (producer) and
      - Triage Worker (consumer).

    Goal: stable, versioned, minimal event shape that supports triage + assignment
    without leaking full raw GitHub payloads into downstream systems.
    """

    # Prevent silent drift: if either side sends unknown fields, validation fails fast.
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(
        default=SCHEMA_VERSION,
        description="Contract version for this message. Used to manage evolution safely.",
        examples=["1.0"],
    )

    event_id: str = Field(
        ...,
        description=("Internal idempotency key for deduplication. For MVP, we will set this equal to delivery_id."),
        examples=["9d3d6c20-2a71-11ef-9a3b-acde48001122"],
    )

    delivery_id: str = Field(
        ...,
        description=("GitHub delivery ID from the X-GitHub-Delivery header (unique per webhook delivery)."),
        examples=["9d3d6c20-2a71-11ef-9a3b-acde48001122"],
    )

    event_name: str = Field(
        ...,
        description='GitHub event type from X-GitHub-Event (e.g., "issues").',
        examples=["issues"],
    )

    action: str = Field(
        ...,
        description='GitHub event action from payload (e.g., "opened", "edited").',
        examples=["opened"],
    )

    received_at: datetime = Field(
        ...,
        description="Timestamp when the gateway accepted the webhook (gateway clock).",
    )

    installation_id: int = Field(
        ...,
        description="GitHub App installation ID associated with the event.",
        examples=[12345678],
    )

    repo: RepoRef = Field(
        ...,
        description="Repository reference for routing/config lookup and audit.",
    )

    issue: IssueRef = Field(
        ...,
        description="Issue snapshot used for triage, classification, and assignment.",
    )

    sender_login: str | None = Field(
        default=None,
        description="GitHub username (login) of the actor that triggered the event (if present).",
        examples=["octocat"],
    )

    trace_id: str | None = Field(
        default=None,
        description=(
            "Correlation ID for distributed tracing/log correlation (e.g., propagated from gateway request context)."
        ),
        examples=["trace-01J2Z8Y6Z3J8Q9K7V5H2K1M0N9"],
    )
