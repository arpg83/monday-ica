import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

# ---------- 6 - monday-list-boards ----------
# Caso positivo
def test_list_boards_success(monkeypatch):
    class MockBoards:
        def fetch_boards(self, limit, page):
            return {"data": {"boards": [{"id": "b1", "name": "Board 1"}]}}
    class MockMondayClient:
        def __init__(self, api_key):
            self.boards = MockBoards()
    monkeypatch.setattr("server.MondayClient", MockMondayClient)

    payload = {"limit": 10, "page": 1}
    response = client.post("/monday/boards/list", json=payload)
    assert response.status_code == 200
    assert "Board 1" in str(response.json())

# Caso negativo: # Falta page
def test_list_boards_invalid_payload():
    payload = {"limit": 10}  
    response = client.post("/monday/boards/list", json=payload)
    assert response.status_code == 422

# ---------- 7 - monday-get-board-groups ----------
# Caso positivo
def test_get_board_groups_success(monkeypatch):
    # Mock que devuelve la estructura real esperada por el endpoint
    class MockGroups:
        def get_groups_by_board(self, board_ids):
            return {
                "data": {
                    "boards": [
                        {
                            "groups": [
                                {"id": "g001", "title": "Backlog"},
                                {"id": "g002", "title": "In Progress"}
                            ]
                        }
                    ]
                }
            }

    class MockMondayClient:
        def __init__(self, api_key):
            self.groups = MockGroups()

    # Reemplazamos MondayClient en server.py por nuestro mock
    monkeypatch.setattr("server.MondayClient", MockMondayClient)

    payload = {"board_id": "b123"}

    response = client.post("/monday/board_groups/get", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Comprobamos que tenga invocationId
    assert "invocationId" in data

    # Validamos que el mensaje incluye datos de los grupos
    assert any("Backlog" in msg["message"] for msg in data["response"])
    assert any("In Progress" in msg["message"] for msg in data["response"])

def test_get_board_groups_empty_success(monkeypatch):
    # Mock que devuelve un board sin grupos
    class MockGroups:
        def get_groups_by_board(self, board_ids):
            return {
                "data": {
                    "boards": [
                        {
                            "groups": []  # Lista vacía
                        }
                    ]
                }
            }

    class MockMondayClient:
        def __init__(self, api_key):
            self.groups = MockGroups()

    # Reemplazamos MondayClient en server.py por nuestro mock
    monkeypatch.setattr("server.MondayClient", MockMondayClient)

    payload = {"board_id": "b123"}

    response = client.post("/monday/board_groups/get", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Comprobamos que tenga invocationId
    assert "invocationId" in data

    # Validamos que el mensaje indique que no hay grupos
    assert any("No se encontraron grupos" in msg["message"] for msg in data["response"])

