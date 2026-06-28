"""Pydantic request and response models for the Sentiment & Urgency Detector."""

from pydantic import BaseModel, Field


class TicketRequest(BaseModel):
    """Incoming ticket to analyze."""

    ticket_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Unique ticket identifier",
        examples=["T-1001"],
    )
    text: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Ticket body text to classify",
    )
    source: str = Field(
        default="manual",
        description="Origin system of the ticket",
        examples=["zendesk", "email", "chat", "manual"],
    )


class AnalyzeResponse(BaseModel):
    """Result returned after classifying a ticket."""

    ticket_id: str
    scores: dict  # full classifier output
    flagged: bool
    alert_reason: str | None = None
    draft_reply: str | None = None


class StatsResponse(BaseModel):
    """Aggregated dashboard statistics."""

    total_tickets: int = 0
    flagged_tickets: int = 0
    avg_sentiment: float = 0.0
    avg_urgency: float = 0.0
    churn_risk_count: int = 0
    tone_distribution: dict = Field(default_factory=dict)
