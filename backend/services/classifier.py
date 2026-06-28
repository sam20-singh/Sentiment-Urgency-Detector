"""Groq API call, system prompt, and JSON parser for ticket classification."""

import asyncio
import json
import logging
import os
import re

from fastapi import HTTPException
from groq import AsyncGroq, AuthenticationError, RateLimitError

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a customer support ticket analyzer.
Analyze the given ticket and return ONLY valid JSON with these exact keys:

{
  "sentiment_score": <integer 0-10, where 0=very positive, 10=furious>,
  "urgency_score": <integer 0-10, where 0=not urgent, 10=critical>,
  "churn_risk": <boolean, true if customer may cancel or leave>,
  "tone": <one of: "angry", "frustrated", "neutral", "confused", "positive">,
  "reason": <string, 1-2 sentence explanation of why you scored it this way>,
  "key_phrases": <list of up to 3 strings that most indicate the tone>
}

Scoring guide:
- sentiment_score >= 7: clearly angry or hostile language
- urgency_score >= 8: mentions business impact, deadlines, or escalation threats
- churn_risk = true: phrases like "cancel", "switch to competitor", "last time",
  "never using again", "requesting refund"

Return ONLY the JSON object. No preamble, no markdown fences.\
"""

MODEL = "llama-3.3-70b-versatile"

MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds


async def classify_ticket(ticket_text: str) -> dict:
    """Send ticket text to Groq LLM and return parsed JSON scores.

    Args:
        ticket_text: Raw ticket body to analyze.

    Returns:
        Dict with sentiment_score, urgency_score, churn_risk, tone,
        reason, and key_phrases.

    Raises:
        HTTPException 401: If the Groq API key is invalid.
        HTTPException 429: If the Groq rate limit is exhausted after retries.
        HTTPException 502: If the model returns unparseable JSON.
        HTTPException 503: If an unexpected network/service error occurs.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY is not set in environment")
        raise HTTPException(
            status_code=401,
            detail="GROQ_API_KEY is not configured. Add it to your .env file.",
        )

    client = AsyncGroq(api_key=api_key)
    last_exception = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                "Classifying ticket (attempt %d/%d, model=%s)",
                attempt, MAX_RETRIES, MODEL,
            )
            chat_completion = await client.chat.completions.create(
                model=MODEL,
                temperature=0.1,
                max_tokens=512,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Ticket:\n\n{ticket_text}"},
                ],
            )
            break  # success

        except AuthenticationError as exc:
            logger.error("Groq authentication failed: %s", exc)
            raise HTTPException(
                status_code=401,
                detail="Invalid GROQ_API_KEY. Please check your .env file and get a valid key from https://console.groq.com/keys",
            ) from exc

        except RateLimitError as exc:
            last_exception = exc
            if attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    "Rate limited by Groq (attempt %d/%d). Retrying in %.1fs…",
                    attempt, MAX_RETRIES, delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error("Groq rate limit exhausted after %d attempts", MAX_RETRIES)
                raise HTTPException(
                    status_code=429,
                    detail="Groq rate limit reached. Please try again in a few minutes.",
                ) from exc

        except Exception as exc:
            logger.error("Unexpected Groq API error: %s", exc)
            raise HTTPException(
                status_code=503,
                detail=f"Classifier service unavailable: {type(exc).__name__}",
            ) from exc

    raw = chat_completion.choices[0].message.content.strip()
    logger.debug("Raw classifier output: %s", raw[:200])

    # Strip markdown fences if the model wrapped the output anyway
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        scores = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse classifier JSON: %s", raw[:300])
        raise HTTPException(
            status_code=502,
            detail="Classifier returned invalid JSON. Please try again.",
        ) from exc

    logger.info(
        "Classification complete — sentiment=%s, urgency=%s, churn=%s, tone=%s",
        scores.get("sentiment_score"),
        scores.get("urgency_score"),
        scores.get("churn_risk"),
        scores.get("tone"),
    )
    return scores
