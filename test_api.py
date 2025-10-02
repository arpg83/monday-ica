from fastapi.testclient import TestClient
from server import app
import json

client =  TestClient(
    app,
    base_url="http://localhost:10000",
    raise_server_exceptions=True,
    root_path="",
    backend="asyncio",
    backend_options=None,
    cookies=None,
    headers=None,
    follow_redirects=True,
    client=("testclient", 50000),
)


def test_read_main():
    # 1. Make a request using the client (simulating a GET request to '/')
    json_post = {
        "limit":"10",
        "page":"0"
    }
    response = client.post(url="/monday/boards/list", content= json.dumps(json_post))
    response_obj = json.load(response)

    # 2. Assert the expected HTTP status code
    assert response.status_code == 200

    # 3. Assert the expected JSON response body
    assert response_obj["status"] == "success"
    assert str(response_obj["response"][0]["message"]).startswith("Tableros disponibles en Monday.com:")