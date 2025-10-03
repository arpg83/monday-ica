import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

# ---------- 20 - monday-delete-group ----------
# Caso positivo
def test_delete_group_success(monkeypatch):
    class MockGroups:
        def delete_group(self, board_id, group_id):
            return {"data": {"delete_group": {"id": group_id}}}

    class MockMondayClient:
        def __init__(self, api_key):
            self.groups = MockGroups()

    monkeypatch.setattr("server.MondayClient", MockMondayClient)

    payload = {
        "board_id": "b123",
        "group_id": "g123"
    }
    response = client.post("/monday/group/delete", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "g123" in str(data)


# Caso negativo: error de conexión
def test_delete_group_connection_error(monkeypatch):
    class MockMondayClient:
        def __init__(self, api_key):
            raise ConnectionError("Simulated connection error")

    monkeypatch.setattr("server.MondayClient", MockMondayClient)

    payload = {
        "board_id": "b123",
        "group_id": "g123"
    }
    response = client.post("/monday/group/delete", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert any("Error" in msg["message"] for msg in data["response"])

# ---------- 21 - monday-delete-item ----------
# Caso positivo
def test_delete_item_success(monkeypatch):
    class MockItems:
        def delete_item_by_id(self, item_id):
            return {"data": {"delete_item": {"id": item_id}}}

    class MockMondayClient:
        def __init__(self, api_key):
            self.items = MockItems()

    monkeypatch.setattr("server.MondayClient", MockMondayClient)

    payload = {
        "item_id": "i123"
    }
    response = client.post("/monday/item/delete", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "i123" in str(data)


# Caso negativo: error de conexión
def test_delete_item_connection_error(monkeypatch):
    class MockMondayClient:
        def __init__(self, api_key):
            raise ConnectionError("Simulated connection error")

    monkeypatch.setattr("server.MondayClient", MockMondayClient)

    payload = {
        "item_id": "i123"
    }
    response = client.post("/monday/item/delete", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert any("Error" in msg["message"] for msg in data["response"])

if __name__ == "__main__":
    pytest.main()    