import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

# ---------- 1 - monday-create-board ----------
def test_create_board_success(monkeypatch):
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


# ---------- 2 - monday-create-board-group ----------
def test_create_board_group_success(monkeypatch):
    class MockGroups:
        def create_group(self, board_id, group_name):
            return {"data": {"create_group": {"id": "g123"}}}

    class MockMondayClient:
        def __init__(self, api_key):
            self.groups = MockGroups()

    monkeypatch.setattr("server.MondayClient", MockMondayClient)

    payload = {
        "board_id": "111",
        "group_name": "Test Group"
    }

    response = client.post("/monday/board_group/create", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "invocationId" in data
    assert any("Test Group" in msg["message"] for msg in data["response"])


# ---------- 3 - monday-create-item ----------
def test_create_item_success(monkeypatch):
    class MockItems:
        def create_item(self, item_name, board_id, group_id, column_values, create_labels_if_missing):
            return {"data": {"create_item": {"id": "i123"}}}

    class MockMondayClient:
        def __init__(self, api_key):
            self.items = MockItems()

    monkeypatch.setattr("server.MondayClient", MockMondayClient)

    payload = {
        "item_name": "Test Item",
        "board_id": "b123",
        "group_id": "g123",
        "column_values": {"status": "Done"},
        "create_labels_if_missing": True
    }

    response = client.post("/monday/item/create", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "invocationId" in data
    assert any("Test Item" in msg["message"] for msg in data["response"])


# ---------- 22 - monday-create-subitem ----------
def test_create_subitem_success(monkeypatch):
    class MockItems:
        def create_subitem(self, subitem_name, parent_item_id, column_values, create_labels_if_missing):
            return {"data": {"create_subitem": {"id": "si456"}}}

    class MockMondayClient:
        def __init__(self, api_key):
            self.items = MockItems()

    monkeypatch.setattr("server.MondayClient", MockMondayClient)

    payload = {
        "subitem_name": "Test Subitem",
        "parent_item_id": "i123",
        "column_values": {"priority": "High"},
        "create_labels_if_missing": False
    }

    response = client.post("/monday/subitem/create", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "invocationId" in data
    assert any("Test Subitem" in msg["message"] for msg in data["response"])


# ---------- 4 - monday-create-update ----------
def test_create_update_comment_success(monkeypatch):
    class MockUpdates:
        def create_update(self, item_id, update_value):
            return {"data": {"create_update": {"id": "u789"}}}

    class MockMondayClient:
        def __init__(self, api_key):
            self.updates = MockUpdates()

    monkeypatch.setattr("server.MondayClient", MockMondayClient)

    payload = {
        "item_id": "i123",
        "update_value": "This is a test comment"
    }

    response = client.post("/monday/comment/update", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "invocationId" in data
    assert any("test comment" in msg["message"].lower() for msg in data["response"])


# ---------- 5 - monday-create-doc ----------
def test_create_doc_success(monkeypatch):
    class MockDocs:
        def create_doc(self, title, workspace_id=None, board_id=None, kind=None, column_id=None, item_id=None):
            return {"data": {"create_doc": {"id": "d001"}}}

    class MockMondayClient:
        def __init__(self, api_key):
            self.docs = MockDocs()

    monkeypatch.setattr("server.MondayClient", MockMondayClient)

    payload = {
        "title": "Test Document",
        "workspace_id": "w123",
        "board_id": "b123",
        "kind": "doc",
        "column_id": "c123",
        "item_id": "i123"
    }

    response = client.post("/monday/doc/create", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "invocationId" in data
    assert any("Test Document" in msg["message"] for msg in data["response"])


# ---------- 5a - monday-create-doc-workspace ----------
def test_create_doc_workspace_success(monkeypatch):
    class MockDocs:
        def create_doc_workspace(self, title, workspace_id, kind):
            return {"data": {"create_doc_workspace": {"id": "dw002"}}}

    class MockMondayClient:
        def __init__(self, api_key):
            self.docs = MockDocs()

    monkeypatch.setattr("server.MondayClient", MockMondayClient)

    payload = {
        "title": "Workspace Doc",
        "workspace_id": "w123",
        "kind": "doc"
    }

    response = client.post("/monday/doc/create/by_workspace", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "invocationId" in data
    assert any("Workspace Doc" in msg["message"] for msg in data["response"])


# ---------- 5b - monday-create-doc-item-column ----------
def test_create_doc_item_success(monkeypatch):
    class MockDocs:
        def create_doc_item(self, title, column_id, item_id):
            return {"data": {"create_doc_item": {"id": "di003"}}}

    class MockMondayClient:
        def __init__(self, api_key):
            self.docs = MockDocs()

    monkeypatch.setattr("server.MondayClient", MockMondayClient)

    payload = {
        "title": "Item Column Doc",
        "column_id": "c123",
        "item_id": "i123"
    }

    response = client.post("/monday/doc/create/by_item_column", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "invocationId" in data
    assert any("Item Column Doc" in msg["message"] for msg in data["response"])


# ---------- 23 - monday-create-column ----------
def test_create_column_success(monkeypatch):
    class MockColumns:
        def create_column(self, board_id, column_title, column_type=None, defaults=None):
            return {"data": {"create_column": {"id": "col004"}}}

    class MockMondayClient:
        def __init__(self, api_key):
            self.columns = MockColumns()

    monkeypatch.setattr("server.MondayClient", MockMondayClient)

    payload = {
        "board_id": "b123",
        "column_title": "Status",
        "column_type": "status",
        "defaults": {"label": "Done"}
    }

    response = client.post("/monday/columns/create", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "invocationId" in data
    assert any("Status" in msg["message"] for msg in data["response"])

#if __name__ == "__main__":
#    pytest.main()