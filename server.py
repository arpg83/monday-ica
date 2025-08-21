""" Module that generates the service for Monday """

from fastapi import FastAPI, Request
from pydantic import BaseModel
import requests
from requests.auth import HTTPBasicAuth
from uuid import uuid4
from typing import Any, Dict, List, Type, TypeVar
import uvicorn
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv
import os
from schemas import ResponseMessageModel, OutputModel, ListGroupBoard
from monday import MondayClient


load_dotenv()

logger = logging.getLogger(__name__)
template_env = Environment(loader=FileSystemLoader("templates"))

T = TypeVar('T', bound=BaseModel)

app = FastAPI()

@app.get("/monday/boards/list")
async def list_users(request: Request) -> OutputModel:
    """
    List Boards from Monday.

    Args:
        limit: Boards Quantitu per page
        page: Number of page
        
    Returns:
        List of Boards
        
    """
    invocation_id = str(uuid4())
    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,
        response=[ResponseMessageModel(message="Conexion error with Monday Client: {e}")]
    )

    data = await request.json()
    params = ListGroupBoard(**data)
    response = monday_client.boards.fetch_boards(limit=params.limit, page=params.page)
    monday_client.users.fetch_users()
    boards = response["data"]["boards"]
    board_list = "\n".join(
        [f"- {board['name']} (ID: {board['id']})" for board in boards]
    )

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message="Available Monday.com Boards:\n{board_list}")]
    )

@app.get("/monday/users/list")
async def list_users(request: Request) -> OutputModel:
    """
    List Users from Monday.

    Args:
        
    Returns:
        List of Users
        
    """
    invocation_id = str(uuid4())
    monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))


    response = monday_client.users.fetch_users()


    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message="Available Monday.com Boards:\n{board_list}")]
    )



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000, log_level="info")