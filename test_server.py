import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_create_board_success(monkeypatch):
    # Mock MondayClient y su método create_board
    class MockBoards:
        def create_board(self, board_name, board_kind):
            return {"data": {"create_board": {"id": "12345"}}}
    class MockMondayClient:
        def __init__(self, api_key):
            self.boards = MockBoards()
    monkeypatch.setattr("server.MondayClient", MockMondayClient)

    payload = {
        "board_name": "Test Board",
        "board_kind": "public"
    }
    response = client.post("/monday/board/create", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "invocationId" in data
    assert any("Test Board" in msg["message"] for msg in data["response"])

def test_create_board_group_success(monkeypatch):
    # Mock MondayClient y su método create_group
    class MockGroups:
        def create_group(self, board_id, group_name):
            return {"data": {"create_group": {"id": "g123"}}}
    class MockMondayClient:
        def __init__(self, api_key):
            self.groups = MockGroups()
    monkeypatch.setattr("server.MondayClient", MockMondayClient)

    payload = {
        "board_id": 111,
        "group_name": "Test Group"
    }
    response = client.post("/monday/board_group/create", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "invocationId" in data
    assert any("Test Group" in msg["message"] for msg in data["response"])

if __name__ == "__main__":
    pytest.main()