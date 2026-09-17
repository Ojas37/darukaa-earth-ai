import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Darukaa.Earth" in data["service"]

def test_chat_multi_turn_flow():
    # Turn 1: Incomplete query
    resp1 = client.post("/api/v1/chat", json={
        "message": "My biodiversity is declining on my farm."
    })
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["needs_clarification"] is True
    assert len(data1["missing_information"]) > 0
    conv_id = data1["conversation_id"]

    # Turn 2: Provide soil carbon
    resp2 = client.post("/api/v1/chat", json={
        "conversation_id": conv_id,
        "message": "My soil carbon is around 0.3% and it is very dry."
    })
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["conversation_id"] == conv_id
    assert "soil_organic_carbon" in data2["profile_summary"]

    # Turn 3: Provide remaining information
    resp3 = client.post("/api/v1/chat", json={
        "conversation_id": conv_id,
        "message": "We only grow wheat in monoculture with 350 mm annual rain in a semi-arid zone."
    })
    assert resp3.status_code == 200
    data3 = resp3.json()
    assert data3["needs_clarification"] is False
    assert "cropping_pattern" in data3["profile_summary"]
    assert "rainfall" in data3["profile_summary"]

    # Check /api/v1/environment/{conv_id}
    env_resp = client.get(f"/api/v1/environment/{conv_id}")
    assert env_resp.status_code == 200
    env_data = env_resp.json()
    assert env_data["soil"]["organic_carbon_percent"]["value"] == 0.3
    assert env_data["land"]["cropping_pattern"]["value"] == "monoculture"
