# Prompt Documentation — Sentinel 

This document chronicles the chronological prompts used to instruct the AI assistant to build the **Sentinel — Sentiment & Urgency Detector** from scratch to its final, production-ready state.

## Phase 1: Core Backend & AI Integration
- *"Build a FastAPI sentiment detector using Groq API with llama-3.3-70b."*
- *"Write an async `classify_ticket` function using `AsyncGroq`. It must use a highly constrained system prompt to instruct the LLM to output pure JSON with the following keys: `sentiment_score` (1-10), `urgency_score` (1-10), `churn_risk` (bool), `tone`, `reason`, and `key_phrases`."*
- *"Create a SQLite schema and `database.py` to persist incoming tickets and calculate aggregate statistics like average sentiment and total flagged tickets."*
- *"Write a Discord webhook integration. It should send a rich red embed containing the ticket text, scores, and reason whenever the threshold logic determines a ticket is high risk."*

## Phase 2: Building the Dashboard
- *"Create a vanilla HTML/CSS/JS frontend dashboard to interact with the API and view stats. Use standard `fetch` API without any build tools."*
- *"I want a pure vanilla frontend (`app.js`, `index.html`, `style.css`), but I want it to be a very good, professional, elite UI."*

## Phase 3: Premium UI/UX Polish
- *"This UI is okay, but improve it. Add a background snow particle effect using an HTML5 canvas."*
- *"The background snow effect is not visible. Make the particles bright white and give the cards sharper contrast."*
- *"Improve the UI further. Add scroll-down reveal animations so sections slide and fade into view as the user scrolls down."*
- *"Add more unique UI effects. I want a premium feel. Add a static fractal noise texture overlay to the background, glowing table row hovers, and a sweeping laser effect on the primary button."*
- *"The current dark theme is too basic. I want a much more premium theme. Change it to an ultra-premium Obsidian (pitch black) and Electric Cyan aesthetic. Replace all hardcoded purples with electric blue/cyan gradients."*

## Phase 4: Agentic Capabilities
- *"Add an AI Agent loop to the backend. The agent should be able to draft replies to the customer. Give the agent access to mock tools like `search_knowledge_base` and `check_customer_account`. Force the LLM to call these tools before formulating the final draft reply."*

## Phase 5: Documentation & Submission
- *"Update the README file. Don't miss any feature. All info must be in the README, including screenshots and a specific structure: Setup Instructions, Run Instructions, Architecture Overview, Assumptions & Limitations."*
- *"Add more extreme details to the README. Include the full tech stack, deep architectural explanations of the Pydantic schemas and background tasks, and exact JSON request/response examples."*
- *"Fulfill these final three project submission requirements: 1. An AI Usage Note (What AI helped with, what it got wrong). 2. A Sample Data Folder with `inputs.json` and `expected_outputs.json`. 3. A Pytest suite covering the happy path with mocked LLM calls."*

---

## 🤖 Core LLM Prompts

### 1. Classifier Prompt (`classifier.py`)
This prompt is the heart of the application, forcing the LLM into structured data extraction without hallucinating markdown.
```text
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
- churn_risk = true: phrases like "cancel", "switch to competitor"

Return ONLY the JSON object. No preamble, no markdown fences.
```

### 2. Agent Drafter Prompt (`agent.py`)
This prompt is used in the multi-step reasoning loop to draft empathetic replies.
```text
You are an expert, professional customer support agent.
Your goal is to draft a helpful, empathetic reply to the customer's ticket.
You MUST use your provided tools to search the knowledge base for accurate answers or check account details before answering.
Once you have gathered the necessary information using tools, formulate the final draft reply.
Keep the draft concise, polite, and directly address the user's problem based on the knowledge base or account data.
Do not use markdown blocks for the final answer, just plain text ready to be sent to the customer.
```
