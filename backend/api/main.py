"""FastAPI app entry point — all routes for the Sentiment & Urgency Detector."""

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv(override=True)  # Must run before any module reads os.environ

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_STATIC_DIR = BASE_DIR / "frontend" / "static"

from backend.services.classifier import classify_ticket
from backend.core.database import delete_ticket, get_all_tickets, get_stats, init_db, save_ticket, delete_all_tickets
from backend.core.discord_alert import send_alert
from backend.models.models import AnalyzeResponse, StatsResponse, TicketRequest
from backend.core.thresholds import should_alert
from backend.services.agent import generate_draft_reply

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sentinel")


# ── App lifespan ──────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise resources on startup; clean up on shutdown."""
    init_db()
    logger.info("🚀 Sentinel is live — http://127.0.0.1:8000")
    yield
    logger.info("Shutting down…")


app = FastAPI(
    title="Sentiment & Urgency Detector",
    description="AI-powered customer support ticket analyzer with Discord alerting",
    version="2.0.0",
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files ──────────────────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory=str(FRONTEND_STATIC_DIR)), name="static")


# ── Routes ────────────────────────────────────────────────────────────────────


@app.get("/", include_in_schema=False)
async def serve_dashboard():
    """Serve the frontend dashboard."""
    return FileResponse(str(FRONTEND_STATIC_DIR / "index.html"))


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_ticket(req: TicketRequest) -> AnalyzeResponse:
    """Classify a support ticket and optionally fire a Discord alert.

    1. Send ticket text to the Groq LLM classifier.
    2. Evaluate threshold rules (sentiment, urgency, churn).
    3. Persist the result to SQLite.
    4. If flagged, post a rich embed to the Discord webhook.
    """
    logger.info("Analyzing ticket %s (source=%s)", req.ticket_id, req.source)
    scores = await classify_ticket(req.text)
    flagged, alert_reason = should_alert(scores)
    
    logger.info("Triggering Agent Loop for %s", req.ticket_id)
    draft_reply = await generate_draft_reply(req.ticket_id, req.text, scores)

    save_ticket(
        ticket_id=req.ticket_id,
        text=req.text,
        scores=scores,
        flagged=flagged,
        alert_reason=alert_reason,
        source=req.source,
        draft_reply=draft_reply,
    )

    if flagged:
        logger.warning("⚠ Ticket %s FLAGGED — %s", req.ticket_id, alert_reason)
        await send_alert(req.text, scores, alert_reason)

    return AnalyzeResponse(
        ticket_id=req.ticket_id,
        scores=scores,
        flagged=flagged,
        alert_reason=alert_reason if flagged else None,
        draft_reply=draft_reply,
    )


@app.get("/tickets")
def list_tickets(flagged_only: bool = False) -> list[dict]:
    """Return stored tickets, optionally filtered to flagged-only."""
    return get_all_tickets(flagged_only)


@app.get("/stats", response_model=StatsResponse)
def dashboard_stats() -> StatsResponse:
    """Return aggregated statistics for the dashboard."""
    data = get_stats()
    return StatsResponse(**data)


@app.delete("/tickets/{ticket_id}")
def remove_ticket(ticket_id: str) -> dict:
    """Delete a ticket by ID."""
    removed = delete_ticket(ticket_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"deleted": ticket_id}


@app.post("/reset")
def reset_database() -> dict:
    """Clear all tickets from the database."""
    removed_count = delete_all_tickets()
    return {"status": "ok", "deleted_count": removed_count}


@app.get("/health")
def health_check() -> dict:
    """Liveness probe that also reports the active model."""
    return {"status": "ok", "model": "llama-3.3-70b-versatile"}
