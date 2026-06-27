# Sentinel — Sentiment & Urgency Detector

> ### 🌐 **[Live Demo → https://sentiment-urgency-detector.onrender.com](https://sentiment-urgency-detector.onrender.com/)**
> **Try it now — no setup required!** The app is deployed and publicly accessible.

Sentinel is a real-time, AI-powered customer support ticket analyzer. Built on a blazing-fast **FastAPI** backend and an ultra-premium vanilla frontend, it uses **Groq Cloud's Llama 3.3 70B** model to instantly evaluate inbound support tickets. 

It automatically scores tickets for **Sentiment (1-10)**, **Urgency (1-10)**, detects the **Tone**, evaluates the **Churn Risk**, and generates a **Draft Reply**. If a ticket is classified as high-risk, Sentinel immediately fires an asynchronous webhook alert to a dedicated **Discord** channel.

DEMO VIDEO LINK : https://drive.google.com/file/d/1VVjRRWWC8ebuuat5KVG---N2jvPlOpsa/view?usp=sharing


---

## 🛠️ Tech Stack

- **Backend Framework**: FastAPI (Python 3.11+)
- **AI Inference Engine**: Groq Cloud API (Llama 3.3 70B Versatile)
- **Database**: SQLite (built-in `sqlite3` module)
- **Alerting**: Discord Webhooks integration (asynchronous)
- **Frontend UI**: Pure Vanilla HTML5, CSS3 (CSS Variables, Grid, Glassmorphism), and Vanilla JavaScript (ES6 Modules, IntersectionObserver)
- **Server**: Uvicorn ASGI Server

---

## Setup Instructions

### Prerequisites
| Requirement | Details |
|---|---|
| **Python** | 3.11 or later installed on your machine |
| **Groq account** | Free tier available — no credit card required |
| **Discord webhook** | A webhook URL for the Discord channel where alerts should be routed |

### 1. Get a Groq API Key
1. Go to <https://console.groq.com> and sign in (or create an account).
2. Navigate to **API Keys** in the left sidebar.
3. Click **Create API Key**, give it a memorable name, and copy the value securely.

### 2. Create a Discord Webhook
1. Open your Discord server and go to **Server Settings → Integrations → Webhooks**.
2. Click **New Webhook**.
3. Choose the target channel, name it (e.g. *Ticket Sentinel*), and click **Copy Webhook URL**.

### 3. Install Dependencies
```bash
# Clone the project repository
git clone <your-repo-url> sentiment-detector
cd sentiment-detector

# Create an isolated virtual environment
python -m venv .venv

# Activate the virtual environment:
# On Windows:
.venv\Scripts\activate
# On macOS / Linux:
source .venv/bin/activate

# Install all required Python packages (FastAPI, Uvicorn, Groq, HTTPX)
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
# Copy the template to create your active .env file
cp .env .env.bak
```
Open the `.env` file in your editor and fill in your keys:
```env
# Your Groq API key starts with gsk_
GROQ_API_KEY=gsk_your_api_key_here

# Your full Discord webhook URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_id/your_webhook_token
```

---

## Run Instructions

1. Start the FastAPI server (now located in `backend/api/`):
   ```bash
   uvicorn backend.api.main:app --reload
   ```
*(The `--reload` flag enables auto-reloading during development. Remove it for production deployments).*

- **Dashboard Access**: The UI is now live at **http://127.0.0.1:8000**.
- **Swagger Documentation**: Interactive API docs are generated automatically and available at **http://127.0.0.1:8000/docs**.

---

## 📝 Sample Ticket Inputs

Copy-paste any of these into the **Ticket Content** field to try the analyzer:

**1. Angry Customer — Billing Issue**
> I've been charged twice for the same subscription this month and nobody is responding to my emails. If this isn't resolved within 24 hours, I'm disputing the charge with my bank and cancelling everything.

**2. Happy Customer — Positive Feedback**
> Just wanted to say your new dashboard update is fantastic! The interface is so much cleaner and faster now. Keep up the amazing work, your team really nailed this release.

**3. Frustrated Customer — Technical Bug**
> My account has been locked for three days now and I can't access any of my saved projects. I've already submitted two tickets with no reply. This is completely unacceptable for a paid plan.

**4. Confused Customer — Feature Question**
> Hi, I'm trying to export my reports as PDF but I can't find the option anywhere. Is this feature available on the free plan or do I need to upgrade? Any help would be appreciated, thanks.

**5. Urgent Escalation — Service Outage**
> Our entire team of 50 people has been unable to log in since this morning. We have a critical client presentation in 2 hours and all our data is on your platform. This needs to be fixed IMMEDIATELY.

---

## Architecture Overview

Sentinel is designed with a modern, lightweight, and blazing fast architecture:

### 1. Frontend (UI/UX)
- **Architecture**: A pure Vanilla HTML/CSS/JS stack, ensuring zero build times, instant hot-reloading, and maximum browser performance.
- **Aesthetic**: Features an ultra-premium Obsidian (pitch black) & Electric Cyan aesthetic utilizing CSS grid, heavy glassmorphism, dynamic background fractal noise textures, and sweeping button lasers.
- **Animations**: Implements an `IntersectionObserver` in JavaScript to trigger performant, hardware-accelerated scroll-reveal animations (`translateY` and `scale`) as elements enter the viewport.
- **State Management**: Asynchronously communicates with the backend via standard `fetch` API, manually updating DOM nodes to reflect real-time ticket ingestion and statistical changes without page reloads.

### 2. Backend (FastAPI)
- **Routing**: Handles static file mounting (`/static`) and RESTful API endpoints.
- **Validation**: Strict schema validation using Pydantic ensures malformed requests are rejected with 422 HTTP responses before touching the database or AI layer.
- **Concurrency**: Fully asynchronous route handlers (`async def`) ensuring the server remains non-blocking during network I/O.

### 3. AI Engine (Groq + Llama 3.3 70B)
- **Inference Speed**: Inbound tickets are sent to Groq's LPU inference engine, resulting in near-instantaneous LLM responses (often >800 tokens/second).
- **Structured Output**: Sentinel utilizes a highly constrained JSON-mode prompt. It forces the LLM to return a strict schema: scores (sentiment 1-10, urgency 1-10), tone description, churn risk boolean, and a contextual auto-drafted reply.

### 4. Data Persistence (SQLite)
- **Local Storage**: A lightweight, file-based SQLite database (`tickets.db`) initialized automatically by `database.py`.
- **Schema**: Tracks `id`, `ticket_id`, `text`, `source`, `sentiment_score`, `urgency_score`, `tone`, `is_churn_risk`, `draft_reply`, `created_at`, and an `is_flagged` boolean.
- **Aggregations**: Executes SQL queries to provide real-time dashboard statistics (`/stats`).

### 5. Alerting System (Discord)
- **Threshold Logic**: Evaluated centrally via `thresholds.py` (e.g. Sentiment <= 3, Urgency >= 8, or Churn Risk = True).
- **Asynchronous Execution**: If thresholds are breached, a Discord alert is dispatched as a FastAPI `BackgroundTasks`. This guarantees the client receives their HTTP response immediately, while the webhook HTTP POST happens safely in the background using `httpx`.
- **Rich Embeds**: Alerts are formatted as rich Discord embeds featuring color-coded threat levels and metric readouts.

---

## Assumptions & Limitations

### Assumptions
- **Language**: The LLM prompt and tone evaluation logic assume English-language customer support tickets. 
- **Traffic Profile**: The local SQLite database assumes moderate traffic typical for an internal tooling dashboard or MVP application.
- **Single Node Setup**: Assumes execution on a single server or container.

### Limitations
- **Rate Limits**: The Groq Cloud free tier strictly limits requests. The `llama-3.3-70b-versatile` model supports approximately ~1,000 requests per day. For enterprise volume, a paid tier or the smaller `llama-3.1-8b-instant` model must be utilized.
- **Database Scale**: SQLite utilizes file-level locking during writes. If deployed globally with hundreds of simultaneous write requests per second, the database will bottleneck. Migration to PostgreSQL is recommended for enterprise scale.
- **Alert Routing**: Webhook alerts route exclusively to a single unified Discord channel. Advanced logic (e.g., routing billing complaints to `#billing` and tech issues to `#engineering`) requires extending the Discord alerting module.
- **Session State**: The frontend does not currently implement persistent web-sockets; it requires manual or automated polling/refreshing to see tickets submitted by *other* users in real-time.

---

## 🔌 Detailed API Endpoints

### `POST /analyze`
Analyzes a support ticket, saves it to the database, and potentially fires an alert.
- **Request Body (JSON)**:
  ```json
  {
    "ticket_id": "T-1001",
    "text": "I demand a refund immediately, your product is broken!",
    "source": "email"
  }
  ```
- **Response**: The full ticket schema including AI-generated scores and draft reply.

### `GET /tickets`
Retrieves a paginated or filtered list of historical tickets.
- **Query Params**: `?flagged_only=true` (optional boolean to filter high-risk tickets only).
- **Response**: A JSON array of ticket objects.

### `GET /stats`
Retrieves aggregated statistics for the dashboard.
- **Response**:
  ```json
  {
    "total_tickets": 150,
    "flagged_tickets": 12,
    "avg_sentiment": 6.8,
    "avg_urgency": 4.2
  }
  ```

### `DELETE /tickets/{ticket_id}`
Permanently deletes a ticket from the SQLite database. Returns status `200 OK` on success.

### `GET /health`
Liveness check for deployment monitoring. Returns `{"status":"ok", "model":"llama-3.3-70b-versatile"}`.

---

## 🚀 Deployment

This application is **live and publicly deployed** on **[Render](https://render.com)** — a free cloud hosting platform for web services.

🔗 **Live URL**: [https://sentiment-urgency-detector.onrender.com](https://sentiment-urgency-detector.onrender.com/)

### Deployment Configuration

| Setting | Value |
|---|---|
| **Platform** | [Render](https://render.com) (Free Tier) |
| **Runtime** | Python 3.11 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT` |
| **Blueprint** | Defined in `render.yaml` |
| **Auto-Deploy** | ✅ Triggered on every push to `main` branch |

### How to Deploy Your Own Instance

1. **Fork** this repository on GitHub.
2. Sign up at [render.com](https://render.com) using your GitHub account (free, no credit card needed).
3. Click **New +** → **Web Service** → connect your forked repo.
4. Render auto-detects settings from `render.yaml`. Verify the build and start commands match the table above.
5. Add the following **Environment Variables** in the Render dashboard:

   | Key | Where to Get It |
   |---|---|
   | `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) → API Keys (free tier available) |
   | `DISCORD_WEBHOOK_URL` | Discord → Server Settings → Integrations → Webhooks |

6. Select the **Free** plan and click **Create Web Service**.
7. Wait ~2–3 minutes for the build to complete. Your app will be live at `https://your-app-name.onrender.com`.

### Free Tier Notes

> ⚠️ Render's free tier spins the service down after **15 minutes of inactivity**. The first request after a sleep period takes ~30–60 seconds (cold start). Subsequent requests are instant.

---

## 📄 License
MIT License. Free for commercial and non-commercial use.
