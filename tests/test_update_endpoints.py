import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

# ---------- 16 - monday-update-item ----------
# Caso positivo
def test_update_item_success(monkeypatch):
    class MockItems:
        def update_item(self, board_id, item_id, column_values, create_labels_if_missing):
            return {"data": {"change_column_values": {"id": item_id}}}
    class MockMondayClient:
        def __init__(self, api_key):
            self.items = MockItems()
    monkeypatch.setattr("server.MondayClient", MockMondayClient)

    payload = {
        "board_id": "b123",
        "item_id": "i123",
        "column_values": {"status": "In Progress"},
        "create_labels_if_missing": True
    }
    response = client.post("/monday/item/update", json=payload)
    assert response.status_code == 200
    assert "i123" in str(response.json())

# Caso negativo: # Falta item_id y demás
def test_update_item_invalid_payload():
    payload = {"board_id": "b123"}  
    response = client.post("/monday/item/update", json=payload)
    assert response.status_code == 422
