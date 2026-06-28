"""Scoring threshold logic and alert decision for ticket classification."""

SENTIMENT_THRESHOLD = 7
URGENCY_THRESHOLD = 8


def should_alert(scores: dict) -> tuple[bool, str]:
    """Determine whether a ticket should trigger a Discord alert.

    Args:
        scores: Classifier output dict containing sentiment_score,
                urgency_score, and churn_risk.

    Returns:
        A tuple of (flagged: bool, reason: str). If no thresholds are
        triggered, reason is an empty string.
    """
    reasons: list[str] = []

    if scores.get("sentiment_score", 0) >= SENTIMENT_THRESHOLD:
        reasons.append(f"High anger score ({scores['sentiment_score']}/10)")

    if scores.get("urgency_score", 0) >= URGENCY_THRESHOLD:
        reasons.append(f"High urgency ({scores['urgency_score']}/10)")

    if scores.get("churn_risk") is True:
        reasons.append("Churn risk language detected")

    if reasons:
        return True, " | ".join(reasons)

    return False, ""
