from fastapi.testclient import TestClient
from server import app
import json

#uv run pytest .\test_api.py -v

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


def test_board_list():
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


def test_board_list_parametros_erronesos():
    #Ingreso parametros erroneos
    json_post = {
        "limit":"pepe",
        "page":"j"
    }
    response = client.post(url="/monday/boards/list", content= json.dumps(json_post))
    response_obj = json.load(response)

    # 2. Assert the expected HTTP status code
    assert response.status_code == 200

    # 3. Assert the expected JSON response body
    assert response_obj["status"] == "error"
    assert str(response_obj["response"][0]["message"]).startswith("Error al procesar el request:")

def test_procesa_archivo_excel_url_erronea():
    json_post = {
        "file_name":"https://pepe.pepe.com/uc?export=download&id=1Csv7aZ1KjXyJyq1AbECI34YzK8n1IpI8",
        "download":"True",
        "rows":"0",
        "uid":"a9c46b18-e8c8-4a6d-98c9-a2c8aea42d0b",
        "continuar":"False",
        "esperar":"True"
    }


    response = client.post(url="/monday/read_excel", content= json.dumps(json_post))
    response_obj = json.load(response)

    # 2. Assert the expected HTTP status code
    assert response.status_code == 200

    # 3. Assert the expected JSON response body
    assert response_obj["status"] == "sucess"
    assert str(response_obj["response"][0]["message"]).startswith("Procesando archivo")
    assert str(response_obj["response"][0]["message"]).find("uid:") > 0
    


def test_estado_proceso_excel():
    json_post = {
        "purgar_inactivos":"false",
        "detener":"false",
        "purgar_procesos_antiguos":"false",
        "uid":"d4ab6534-1e36-4be8-8874-1e04f799511b"
    }

    response = client.post(url="/monday/estado_proceso_excel", content= json.dumps(json_post))
    response_obj = json.load(response)

    # 2. Assert the expected HTTP status code
    assert response.status_code == 200

    # 3. Assert the expected JSON response body
    assert response_obj["status"] == "sucess"
    assert str(response_obj["response"][0]["message"]).startswith("Procesos activos:")


def test_estado_proceso_excel_purga_inactivos():
    json_post = {
        "purgar_inactivos":"true",
        "detener":"false",
        "purgar_procesos_antiguos":"false",
        "uid":""
    }

    response = client.post(url="/monday/estado_proceso_excel", content= json.dumps(json_post))
    response_obj = json.load(response)

    # 2. Assert the expected HTTP status code
    assert response.status_code == 200

    # 3. Assert the expected JSON response body
    assert response_obj["status"] == "sucess"
    #assert str(response_obj["response"][0]["message"]).find("purgo:") > 0

def test_estado_proceso_excel_purga_procesos_antiguos():
    json_post = {
        "purgar_inactivos":"false",
        "detener":"false",
        "purgar_procesos_antiguos":"true",
        "uid":""
    }

    response = client.post(url="/monday/estado_proceso_excel", content= json.dumps(json_post))
    response_obj = json.load(response)

    # 2. Assert the expected HTTP status code
    assert response.status_code == 200

    # 3. Assert the expected JSON response body
    assert response_obj["status"] == "sucess"
    #assert str(response_obj["response"][0]["message"]).find("Se purgaron los procesos inactivos") > 0