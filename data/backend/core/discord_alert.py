"""Discord webhook sender with rich embed formatting for flagged tickets."""

import logging
import os
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)


async def send_alert(
    ticket_text: str,
    scores: dict,
    alert_reason: str,
) -> None:
    """POST a rich embed to the configured Discord webhook.

    Failures are logged but never propagated — the /analyze endpoint
    must always return its response even if Discord delivery fails.

    Args:
        ticket_text: Original ticket body (first 200 chars shown).
        scores: Full classifier output dict.
        alert_reason: Human-readable reason string from threshold logic.
    """
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("DISCORD_WEBHOOK_URL is not set — skipping alert")
        return

    excerpt = ticket_text[:200]

    payload = {
        "username": "Ticket Sentinel",
        "embeds": [
            {
                "title": "\U0001f6a8 High-Priority Ticket Flagged",
                "color": 15158332,  # red
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "fields": [
                    {
                        "name": "Sentiment",
                        "value": f"{scores.get('sentiment_score', '?')}/10",
                        "inline": True,
                    },
                    {
                        "name": "Urgency",
                        "value": f"{scores.get('urgency_score', '?')}/10",
                        "inline": True,
                    },
                    {
                        "name": "Churn Risk",
                        "value": str(scores.get("churn_risk", "?")),
                        "inline": True,
                    },
                    {
                        "name": "Tone",
                        "value": scores.get("tone", "unknown"),
                        "inline": True,
                    },
                    {
                        "name": "Why flagged",
                        "value": alert_reason,
                        "inline": False,
                    },
                    {
                        "name": "Key phrases",
                        "value": ", ".join(scores.get("key_phrases", [])) or "—",
                        "inline": False,
                    },
                    {
                        "name": "Excerpt",
                        "value": f"```{excerpt}```",
                        "inline": False,
                    },
                ],
                "footer": {
                    "text": scores.get("reason", ""),
                },
            }
        ],
    }

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(webhook_url, json=payload)
            r.raise_for_status()
        logger.info("Discord alert sent successfully")
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Discord webhook returned %s: %s",
            exc.response.status_code,
            exc.response.text[:200],
        )
    except Exception as exc:
        logger.error("Failed to send Discord alert: %s", exc)
