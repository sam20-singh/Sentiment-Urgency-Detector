import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

# Must import from main to access the FastAPI app
from backend.api.main import app
import backend.core.database as database

# Initialize the test client
client = TestClient(app)

# Override the database dependency or use the local one since sqlite is fine for tests.
# Since database.init_db() is called on startup, we just use the default tickets.db
# For a perfectly clean test we'd use a temp db, but for submission happy path this is fine.

@pytest.fixture(autouse=True)
def setup_db():
    database.init_db()
    yield

def test_health_check():
    """Test the /health endpoint happy path."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "model" in response.json()

def test_get_tickets():
    """Test retrieving tickets."""
    response = client.get("/tickets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_stats():
    """Test retrieving dashboard stats."""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_tickets" in data
    assert "avg_sentiment" in data
    assert "avg_urgency" in data

@patch("backend.api.main.classify_ticket", new_callable=AsyncMock)
@patch("backend.api.main.generate_draft_reply", new_callable=AsyncMock)
@patch("backend.api.main.send_alert", new_callable=AsyncMock)
def test_analyze_ticket_happy_path(mock_discord, mock_draft, mock_classify):
    """Test analyzing a ticket with mocked AI and Webhook dependencies."""
    
    # Setup mocks
    mock_classify.return_value = {
        "sentiment_score": 2,
        "urgency_score": 9,
        "churn_risk": True,
        "tone": "frustrated",
        "reason": "Customer is blocked and angry.",
        "key_phrases": ["unacceptable", "blocked"]
    }
    mock_draft.return_value = "I am so sorry for the delay. We are escalating this immediately."
    
    # Define test payload
    payload = {
        "ticket_id": "TEST-12345",
        "text": "This is unacceptable! We are blocked.",
        "source": "test"
    }
    
    # Execute
    response = client.post("/analyze", json=payload)
    
    # Assert HTTP response
    assert response.status_code == 200
    data = response.json()
    
    # Validate structure
    assert data["ticket_id"] == "TEST-12345"
    assert data["scores"]["sentiment_score"] == 2
    assert data["flagged"] is True
    assert data["draft_reply"] == "I am so sorry for the delay. We are escalating this immediately."
    
    # Assert our mocks were called
    mock_classify.assert_called_once_with("This is unacceptable! We are blocked.")
    mock_draft.assert_called_once_with(
        "TEST-12345",
        "This is unacceptable! We are blocked.",
        {
            "sentiment_score": 2,
            "urgency_score": 9,
            "churn_risk": True,
            "tone": "frustrated",
            "reason": "Customer is blocked and angry.",
            "key_phrases": ["unacceptable", "blocked"]
        }
    )
