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
from schemas import ResponseMessageModel, OutputModel


load_dotenv()

logger = logging.getLogger(__name__)
template_env = Environment(loader=FileSystemLoader("templates"))

T = TypeVar('T', bound=BaseModel)

app = FastAPI()

@app.get("/monday/users/list")
async def list_users(request: Request) -> OutputModel:
    """
    List users from Monday.

    Args:
        

    Returns:
        
    """
    invocation_id = str(uuid4())
    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message="hola mundo")]
    )
   


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000, log_level="info")
