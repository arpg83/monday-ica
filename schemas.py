from pydantic import BaseModel, Field
from typing import Optional, List

class ResponseMessageModel(BaseModel):
    message: str
    type: str = "text"

class OutputModel(BaseModel):
    status: str = Field(default="success")
    invocationId: str
    response: List[ResponseMessageModel]

class ListGroupBoard(BaseModel):
    limit: int
    page: int

class CreateBoard(BaseModel):
    board_name: str
    board_kind: str
