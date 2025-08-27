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
from schemas import ResponseMessageModel, OutputModel, CreateBoardParams, CreateBoardGroupParams, CreateItemParams, ListBoardsParams, GetBoardGroupsParams, UpdateItemParams, CreateUpdateCommentParams,FetchItemsByBoardId
#, CreateUpdateParams, CreateUpdateItemParams
from monday import MondayClient
from monday.resources.types import BoardKind
from fastapi.responses import JSONResponse


load_dotenv()

logging.basicConfig(

    level=logging.INFO,

    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",

    datefmt="%Y-%m-%d %H:%M:%S",

)

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

@app.get("/monday/board_groups/get")
async def getBoardGroups(request: Request) -> OutputModel:
    """
    Get the Groups of a Monday.com Board.

    Args: 
        board_id
        
    Returns:
        List of Groups
        
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
    params = GetBoardGroupsParams(**data)
    response = monday_client.groups.get_groups_by_board(board_ids=params.board_id)

    groups = response["data"]["groups"]
    group_list = "\n".join(
        [f"- {group['title']} (ID: {group['id']})" for group in groups]
    )
    message = "Available Monday.com Groups: \n %s" % (group_list) 

    #message = f"Available Monday.com Groups: \n %s" % (response['data']) 

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
    )

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
        logger.info(board_name)
        message = f"{message}  Board: {board_name}"
        items_page = board["items_page"]
        if "cursor" in items_page:
            cursor = items_page["cursor"]
            message = f"{message}  Cursor: {cursor}"
            items = items_page["items"]
            for item in items:
                group = item["group"]
                column_values = item["column_values"]
                id = item["id"]
                name = item["name"]
                logger.info(name)
                message = f"{message}  item name: {name}"
                message = f"{message}  id: {id}"
                if "column_values" in item:
                    column_values = item["column_values"]
                    for column in column_values:
                        col_id = column["id"]
                        text = column["text"]
                        message = f"{message}  Column id: {col_id}"
                        message = f"{message}  Column text: {text}"

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
    )

#    message = "Épicas"
#    content = {"message":message}
#    headers = {'Content-Disposition': 'inline; filename="out.json"'}

#    return JSONResponse(
#        content=content,
#        headers=headers
#    )

    
@app.post("/monday/board_group/create")
async def create_board_group(request: Request) -> OutputModel:
    """
    Create a new group in a Monday.com board.

    Args:
        monday_client (MondayClient): The Monday.com client.
        board_id (str): The ID of the board.
        group_name (str): The name of the group.

    Returns: 

    """
    invocation_id = str(uuid4())
    data = await request.json()
    params = CreateBoardGroupParams(**data)
    monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))

    group = monday_client.groups.create_group(board_id=params.board_id, group_name=params.group_name)
    
    message = f"Created new group: {params.group_name} in board: {params.board_id}. ID of the group: {group['data']['create_group']['id']}"

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
    )

@app.post("/monday/doc/create")
async def create_doc(request: Request) -> OutputModel:
    '''
    
    '''


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
    monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
     
    if params.parent_item_id is None and params.group_id is not None:
        response = monday_client.items.create_item(
            board_id=params.board_id,
            group_id=params.group_id,
            item_name=params.item_name,
            column_values=params.columns_values,
        )
    elif params.parent_item_id is not None and params.group_id is None:
        response = monday_client.items.create_subitem(
            parent_item_id=params.parent_item_id,
            subitem_name=params.item_name,
            column_values=params.columns_values,
        )
    else:

        message = "You can set either Group ID or Parent Item ID argument, but not both."

        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )

    try:
        data = response["data"]
        id_key = "create_item" if params.parent_item_id is None else "create_subitem"
        #item_url = f"{MONDAY_WORKSPACE_URL}/boards/{params.board_id}/pulses/{data.get(id_key).get('id')}"

        if params.parent_item_id is None and params.group_id is not None:
            message = f"Created a new Monday.com item: {params.item_name} on board Id: {params.board_id} and group Id: {params.group_id}."   
        elif params.parent_item_id is not None and params.group_id is None:
             message = f"Created a new Monday.com item: {params.parent_item_id} on board Id: {params.board_id}."       
        else:
            message = f"Created a new Monday.com item: {params.item_name} on board Id: {params.board_id}."       

        return OutputModel(
                    invocationId=invocation_id,
                    response=[ResponseMessageModel(message=message)]
        )
    
    except Exception as e:

            message = f"Error creating Monday.com item: {e}"

            return OutputModel(
                    invocationId=invocation_id,
                    response=[ResponseMessageModel(message=message)]
            )

@app.put("/monday/comment/update")
async def create_update_comment(request: Request) -> OutputModel:    
    """
    Create an update (comment) on a Monday.com Item or Sub-item.

    Args:
        params: Parameters for updating the item .

    Returns:
        Response with the updated item details.
    """
    invocation_id = str(uuid4())
    data = await request.json()
    params = UpdateItemParams(**data)
    monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))

 
@app.put("/monday/item/update")
async def update_item(request: Request) -> OutputModel:
    """
    Update a Monday.com item's or sub-item's column values.

    Args:
        params: Parameters for updating the item .

    Returns:
        Response with the updated item details.
    """
    invocation_id = str(uuid4())
    data = await request.json()
    params = UpdateItemParams(**data)
    monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    

    response = monday_client.items.change_multiple_column_values(
        board_id=params.board_id, item_id=params.item_id, column_values=params.columns_values
    )

    message = f"Updated Monday.com item. {params.item_id} on board Id: {params.board_id}."  
    # Faltan los valores de las columnas 
        
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