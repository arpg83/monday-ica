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
from schemas import ResponseMessageModel, OutputModel, CreateBoardParams, CreateGroupInBoardParams, CreateItemParams, CreateUpdateParams, CreateUpdateItemParams, ListBoardsParams,FetchItemsByBoardId
from monday import MondayClient
from monday.resources.types import BoardKind


load_dotenv()

logger = logging.getLogger(__name__)
template_env = Environment(loader=FileSystemLoader("templates"))

T = TypeVar('T', bound=BaseModel)

app = FastAPI()

@app.post("/monday/boards/list")
async def listBoards(request: Request) -> OutputModel:    
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
    params = ListBoardsParams(**data)
    response = monday_client.boards.fetch_boards(limit=params.limit, page=params.page)
    boards = response["data"]["boards"]
    board_list = "\n".join(
        [f"- {board['name']} (ID: {board['id']})" for board in boards]
    )
    message = "Available Monday.com Boards: \n %s" % (board_list) 

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
    )

@app.get("/monday/users/list")
async def listUsers(request: Request) -> OutputModel:
    """
    List Users from Monday.

    Args:
        
    Returns:
        List of Users
        
    """
    invocation_id = str(uuid4())
    monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))

    response = monday_client.users.fetch_users()
    users = response["data"]["users"]
    users_list = "\n".join(
        [f"- {user['name']} (ID: {user['id']})" for user in users]
    )

    message = "Available Monday.com Users: \n %s" % (users_list) 

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
    )

#monday-get-board-groups: Retrieves all groups from a specified Monday.com board
#monday-get-item-updates: Retrieves updates/comments for a specific item
#monday-get-docs: Lists documents in Monday.com, optionally filtered by folder
#monday-get-doc-content: Retrieves the content of a specific document

#monday-list-boards: Lists all available Monday.com boards
#monday-list-items-in-groups: Lists all items in specified groups of a Monday.com board
#monday-list-subitems-in-items: Lists all sub-items for given Monday.com items

#monday-create-board: Creates a new Monday.com board
#monday-create-board-group: Creates a new group in a Monday.com board
#monday-create-doc: Creates a new document in Monday.com
#monday-create-item: Creates a new item or sub-item in a Monday.com board
#monday-create-update: Creates a comment/update on a Monday.com item

@app.post("/monday/board/create")
async def create_board(request: Request) -> OutputModel:
    """
    Create a new Monday.com board.

    Args:
        board_name (str): The name of the board.
        board_kind (str): The kind of board to create. Must be one of "public" or "private".

    Returns:

    """
    invocation_id = str(uuid4())
    data = await request.json()
    params = CreateBoardParams(**data)
    monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))

    actual_board_kind = BoardKind(params.board_kind)
    board = monday_client.boards.create_board(
        board_name=params.board_name, board_kind=actual_board_kind
    )

    message = f"Created monday board {params.board_name} of kind {params.board_kind}. ID of the new board: {board['data']['create_board']['id']}"

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
    )

@app.post("/monday/board/fetch_items_by_board_id")
async def fetch_items_by_board_id(request: Request) -> OutputModel:
    """
    Create a new Monday.com board.

    Args:
        board_name (str): The name of the board.
        board_kind (str): The kind of board to create. Must be one of "public" or "private".

    Returns:

    """
    invocation_id = str(uuid4())
    data = await request.json()
    params = FetchItemsByBoardId(**data)
    monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))

    
    board = monday_client.boards.fetch_items_by_board_id(
        board_ids= params.board_id
    )    
    #print(board)
    #print(board["data"])
    message = f"Informacion del Board id: {params.board_id}"
    
    for board in board["data"]["boards"]:
        board_name = board["name"]
        message = f"{message}  Board: {board_name}"
        items_page = board["items_page"]
        print(items_page)
        print("item_page")
        if "cursor" in items_page:
            print(items_page)
            cursor = items_page["cursor"]
            message = f"{message}  Cursor: {cursor}"
            items = items_page["items"]
            for item in items:
                group = item["group"]
                column_values = item["column_values"]
                id = item["id"]
                name = item["name"]
                message = f"{message}  item name: {name}"
                message = f"{message}  id: {id}"
                if "column_values" in item:
                    column_values = item["column_values"]
                    for column in column_values:
                        col_id = column["id"]
                        text = column["text"]
                        message = f"{message}  Column id: {col_id}"
                        message = f"{message}  Column text: {text}"

        
        print(items_page)
    

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
    )

    
@app.post("/monday/board_group/create")
async def create_board_group(request: Request) -> OutputModel:
    """
    Create a new group in a Monday.com board.

    Args:
        params: Parameters for creating the group .

    Returns:
        Response with the created group details.
    """
    invocation_id = str(uuid4())
    data = await request.json()
    params = CreateGroupInBoardParams(**data)
    instance_url = os.getenv("MONDAY_INSTANCIA")   

    # Build request data
    data = {
        "board_id": params.board_id,
    }

    if params.group_name:
        data["group_name"] = params.group_name
    
    headers = {"Accept": "application/json"}

    # Make request
    try:
        response = requests.post(           
            json=data,
            headers=headers,
            auth=HTTPBasicAuth(os.getenv("MONDAY_USUARIO"), os.getenv("MONDAY_CONTRASENA"))
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        response_template = template_env.get_template("response_template_group_board_created.jinja")
        rendered_response = response_template.render(
            board_id=result.get("board_id"),
            group_name=result.get("group_name"),
        )

        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=rendered_response)]
        )
    
    except requests.RequestException as e:
        logger.error(f"Failed to create group on board: {e}")
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Failed to create group on board: {str(e)}")]
        )    

@app.post("/monday/item/create")
async def create_item(request: Request) -> OutputModel:
    """
    Create a new item in a Monday.com Board. Optionally, specify the parent Item ID to create a Sub-item.

    Args:
        params: Parameters for creating the item .

    Returns:
        Response with the item details.
    """
    invocation_id = str(uuid4())
    data = await request.json()
    params = CreateItemParams(**data)
    instance_url = os.getenv("MONDAY_INSTANCIA")    

    # Build request data
    data = {
        "board_id": params.board_id,
    }

    if params.item_name:
        data["item_name"] = params.item_name
    if params.group_id:
        data["group_id"] = params.group_id 
    if params.parent_item_id:
        data["parent_item_id"] = params.parent_item_id
    if params.columns_values:
        data["columns_values"] = params.columns_values                  
    
    headers = {"Accept": "application/json"}

    # Make request
    try:
        response = requests.post(           
            json=data,
            headers=headers,
            auth=HTTPBasicAuth(os.getenv("MONDAY_USUARIO"), os.getenv("MONDAY_CONTRASENA"))
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        response_template = template_env.get_template("response_template_item_created.jinja")
        rendered_response = response_template.render(
            board_id=result.get("board_id"),
            item_name=result.get("item_name"),
            group_id=result.get("group_id"),
            parent_item_id=result.get("parent_item_id"),
            columns_values=result.get("columns_values")
        )

        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=rendered_response)]
        )
    
    except requests.RequestException as e:
        logger.error(f"Failed to create item: {e}")
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Failed to create item: {str(e)}")]
        )    

@app.put("/monday/item/update")
async def create_update(request: Request) -> OutputModel:    
    """
    Create an update (comment) on a Monday.com Item or Sub-item.

    Args:
        params: Parameters for updating the item .

    Returns:
        Response with the updated item details.
    """
    
    invocation_id = str(uuid4())
    headers = {"Accept": "application/json"}
    data = await request.json()
    params = CreateUpdateParams(**data)
    instance_url = os.getenv("MONDAY_INSTANCIA")
 
    # Build request data
    data = {}

    if params.short_desitemIdcription:
        data["item_id"] = params.item_id
    if params.update_text:
        data["update_text"] = params.update_text

    # Make request
    try:
        response = requests.put(           
            json=data,
            headers=headers,
            auth=HTTPBasicAuth(os.getenv("MONDAY_USUARIO"), os.getenv("MONDAY_CONTRASENA"))
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        response_template = template_env.get_template("response_template_item_updated.jinja")
        rendered_response = response_template.render(
            success=True,
            item_id=result.get("item_id"),
            update_text=result.get("update_text")
        )

        return OutputModel(
            status="success",
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=rendered_response)]
        )

    except requests.RequestException as e:
        response_template = template_env.get_template("response_template_item_updated.jinja")
        message = response_template.render(
            success=False,
            error_message=f"Failed to update item: {str(e)}"
        )
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

@app.put("/monday/item/update")
async def create_update_item(request: Request) -> OutputModel:
    """
    Update a Monday.com item's or sub-item's column values.

    Args:
        params: Parameters for updating the item .

    Returns:
        Response with the updated item details.
    """
    
    invocation_id = str(uuid4())


    headers = {"Accept": "application/json"}
    data = await request.json()
    params = CreateUpdateItemParams(**data)
    instance_url = os.getenv("MONDAY_INSTANCIA")
    
    # Build request data
    data = {}

    if params.board_id:
        data["board_id"] = params.board_id
    if params.item_id:
        data["item_id"] = params.item_id     
    if params.monday_client:
        data["monday_client"] = params.monday_client
    if params.columns_values:
        data["columns_values"] = params.columns_values

    # Make request
    try:
        response = requests.put(           
            json=data,
            headers=headers,
            auth=HTTPBasicAuth(os.getenv("MONDAY_USUARIO"), os.getenv("MONDAY_CONTRASENA"))
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        response_template = template_env.get_template("response_template_item_updated.jinja")
        rendered_response = response_template.render(
            success=True,
            item_id=result.get("item_id"),
            board_id=result.get("board_id")
        )

        return OutputModel(
            status="success",
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=rendered_response)]
        )

    except requests.RequestException as e:
        response_template = template_env.get_template("response_template_item_updated.jinja")
        message = response_template.render(
            success=False,
            error_message=f"Failed to update item: {str(e)}"
        )
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

#monday-add-doc-block: Adds a block to an existing document
#monday-move-item-to-group: Moves a Monday.com item to a different group
#monday-archive-item: Archives a Monday.com item

#monday-delete-item: Deletes a Monday.com item
'''
async def create_update_on_item(
    itemId: str,
    updateText: str,
    monday_client: MondayClient,
) -> list[types.TextContent]:
    monday_client.updates.create_update(item_id=itemId, update_value=updateText)
    return [
        types.TextContent(
            type="text", text=f"Created new update on Monday.com item: {updateText}"
        )
    ]
'''
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000, log_level="info")