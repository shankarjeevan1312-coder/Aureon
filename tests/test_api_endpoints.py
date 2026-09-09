import pytest
from starlette.testclient import TestClient
from aureon.server.api import app

client = TestClient(app)

def test_status_endpoint():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["assistant_name"] == "AUREON"
    assert "telemetry" in data
    assert "cpu_percent" in data["telemetry"]

def test_memory_endpoint():
    response = client.get("/api/memory")
    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["github_username"] == "revanthbarthu"

def test_chat_telemetry_query():
    response = client.post("/api/chat", json={"message": "What is my CPU and RAM status?"})
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert len(data["text"]) > 0

def test_chat_destructive_quarantine():
    response = client.post("/api/chat", json={"message": "delete file test_danger.txt"})
    assert response.status_code == 200
    data = response.json()
    # Must have pending_confirmation
    assert data["pending_confirmation"] is not None
    assert data["pending_confirmation"]["name"] == "delete_file"
