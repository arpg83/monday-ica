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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from schemas import ResponseMessageModel, OutputModel, CreateBoardParams, CreateBoardGroupParams, CreateItemParams, ListBoardsParams, GetBoardGroupsParams, UpdateItemParams, CreateUpdateCommentParams,FetchItemsByBoardId,DeleteItemByIdParams,MoveItemToGroupId,CreateColumn
#, CreateUpdateParams, CreateUpdateItemParams
=======
from schemas import ResponseMessageModel, OutputModel, CreateBoardParams, CreateBoardGroupParams, CreateItemParams, ListBoardsParams, GetBoardGroupsParams, UpdateItemParams, CreateUpdateCommentParams,FetchItemsByBoardId,DeleteItemByIdParams,MoveItemToGroupId, CreateUpdateCommentParams
>>>>>>> Stashed changes
=======
from schemas import ResponseMessageModel, OutputModel, CreateBoardParams, CreateBoardGroupParams, CreateItemParams, ListBoardsParams, GetBoardGroupsParams, UpdateItemParams, CreateUpdateCommentParams,FetchItemsByBoardId,DeleteItemByIdParams,MoveItemToGroupId, CreateUpdateCommentParams
>>>>>>> Stashed changes
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
       
    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Conexion error with Monday Client: {e}")]
    )    
      
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

#monday-get-item-updates: Retrieves updates/comments for a specific item
#monday-get-docs: Lists documents in Monday.com, optionally filtered by folder
#monday-get-doc-content: Retrieves the content of a specific document
#monday-list-boards: Lists all available Monday.com boards
#monday-list-items-in-groups: Lists all items in specified groups of a Monday.com board
#monday-list-subitems-in-items: Lists all sub-items for given Monday.com items
#monday-create-doc: Creates a new document in Monday.com
#monday-add-doc-block: Adds a block to an existing document
#monday-archive-item: Archives a Monday.com item


#monday-get-board-groups: Retrieves all groups from a specified Monday.com board
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

#monday-create-board: Creates a new Monday.com board
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

    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Conexion error with Monday Client: {e}")]
    )

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
    fetch items by borard id

    Args:
        board_id (str): The id of the board.

    Returns:

    """
    invocation_id = str(uuid4())
    data = await request.json()
    params = FetchItemsByBoardId(**data)

    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Conexion error with Monday Client: {e}")]
    )
    
    board = monday_client.boards.fetch_items_by_board_id(
        board_ids= params.board_id
    )    
    logger.debug(board)
    #print(board["data"])
    message = f"Informacion del Board id: {params.board_id}"
    
    for board in board["data"]["boards"]:
        board_name = board["name"]
        logger.info(board)
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

<<<<<<< Updated upstream
<<<<<<< Updated upstream
#monday-create-board-group: Creates a new group in a Monday.com board
=======
#monday-create-board-group: Creates a new group in a Monday.com board    
>>>>>>> Stashed changes
=======
#monday-create-board-group: Creates a new group in a Monday.com board    
>>>>>>> Stashed changes
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

    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Conexion error with Monday Client: {e}")]
    )

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

#monday-create-item: Creates a new item or sub-item in a Monday.com board
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
    params = None

    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Conexion error with Monday Client: {e}")]
    )

    message = ""
    response = None
    params = None
    try:
        params = CreateItemParams(**data)
    except Exception as e:
        message = f"Error creating Monday.com item: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    if params.parent_item_id is None and params.group_id is not None:
    #if "board_id" in data:
        logger.info("Creacion item")
        try:
            response = monday_client.items.create_item(
                board_id=params.board_id,
                group_id=params.group_id,
                item_name=params.item_name,
                column_values=params.columns_values,
            )
            logger.info(response)
        except Exception as e:

            message = f"Error creating Monday.com item: {e}"

            return OutputModel(
                    invocationId=invocation_id,
                    response=[ResponseMessageModel(message=message)]
            )
    elif params.parent_item_id is not None and params.group_id is None:
    #elif "parent_item_id" in data:
        logger.info("Creacion sub item")
        try:
            response = monday_client.items.create_subitem(
                parent_item_id=params.parent_item_id,
                subitem_name=params.item_name,
                column_values=params.columns_values
            )
            logger.info(response)
        except Exception as e:

            message = f"Error creating Monday.com item: {e}"

            return OutputModel(
                    invocationId=invocation_id,
                    response=[ResponseMessageModel(message=message)]
            )
    else:
        message = "You can set either Group ID or Parent Item ID argument, but not both."
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )

    try:
        #hay dos tipos de response posibles el la creacion del item y el de la creacion del sub item validar que tipo de response es antes de mapear la respuesta
        data = response["data"]
        #id_key = "create_item" if params.parent_item_id is None else "create_subitem"
        #item_url = f"{MONDAY_WORKSPACE_URL}/boards/{params.board_id}/pulses/{data.get(id_key).get('id')}"

        if params.parent_item_id is None and params.group_id is not None:
        #if "board_id" in data:
            message = f"Created a new Monday.com item: {params.item_name} on board Id: {params.board_id} and group Id: {params.group_id}."   
        elif params.parent_item_id is not None and params.group_id is None:
        #elif "parent_item_id" in data:
             message = f"Created a new Monday.com sub item: {params.parent_item_id} on board Id: {params.board_id}."       
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

#monday-create-update: Creates a comment/update on a Monday.com item
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

    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Conexion error with Monday Client: {e}")]
    )

    data = await request.json()
    params = None  

    try:
        params = CreateUpdateCommentParams(**data)
    except Exception as e:
        message = f"Error Creating an update (comment) on a Monday.com Item or Sub-item: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    response = None
    try:
        #llamada al servicio de monday
        response = monday_client.updates.create_update(item_id=params.item_id, update_value=params.update_text)

        #Imprimo la respuesta
        logger.info(response)
    except Exception as e:
        message = f"Error Creating an update (comment) on a Monday.com Item or Sub-item: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    message = ""
    if not response is None:
        #Genero el mensaje de salida
        logger.info("Procesa respuesta")        
        message = f"Created new update on Monday.com item: {response['data']['create_update']['id']}"
    else:
        logger.info("sin respuesta")
<<<<<<< Updated upstream

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

#monday-update-item: Update a Monday.com item's or sub-item's column values. 
@app.put("/monday/item/update")
async def update_item(request: Request) -> OutputModel:
    '''Update a Monday.com item's or sub-item's column values.

    Args:
        boardId: Monday.com Board ID that the Item or Sub-item is on.
        itemId: Monday.com Item or Sub-item ID to update the columns of.
        columnValues: Dictionary of column values to update the Monday.com Item or Sub-item with. ({column_id: value}).
    '''
 
    invocation_id = str(uuid4())

    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Conexion error with Monday Client: {e}")]
    )

    data = await request.json()
    params = None  

=======

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

#monday-update-item: Update a Monday.com item's or sub-item's column values. 
@app.put("/monday/item/update")
async def update_item(request: Request) -> OutputModel:
    '''Update a Monday.com item's or sub-item's column values.

    Args:
        boardId: Monday.com Board ID that the Item or Sub-item is on.
        itemId: Monday.com Item or Sub-item ID to update the columns of.
        columnValues: Dictionary of column values to update the Monday.com Item or Sub-item with. ({column_id: value}).
    '''
 
    invocation_id = str(uuid4())

    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Conexion error with Monday Client: {e}")]
    )

    data = await request.json()
    params = None  

>>>>>>> Stashed changes
    try:
        params = UpdateItemParams(**data)
    except Exception as e:
        message = f"Error Updating a Monday.com item's or sub-item's column values: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    response = None
    try:
        #llamada al servicio de monday
        response = monday_client.items.change_multiple_column_values(
            board_id=params.board_id, 
            item_id=params.item_id, 
            column_values=params.columns_values
    )

        #Imprimo la respuesta
        logger.info(response)
    except Exception as e:
        message = f"Error Updating a Monday.com item's or sub-item's column values: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    message = ""
    if not response is None:
        #Genero el mensaje de salida
        logger.info("Procesa respuesta")        
        message = f"Updated Monday.com item. {response['data']['change_multiple_column_values']['id']}"
        # message = f"Updated Monday.com item. {params.item_id} on board Id: {params.board_id}."  
        # Faltan los valores de las columnas 
    else:
        logger.info("sin respuesta")

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

#monday-delete-item: Deletes a Monday.com item
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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

#monday-delete-item: Deletes a Monday.com item
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
@app.delete("/monday/item/delete")
async def delete_item_by_id(request: Request) -> OutputModel:
    """Delete item by id args item_id"""
    invocation_id = str(uuid4())

    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,
        status="error",        
        response=[ResponseMessageModel(message="Conexion error with Monday Client: {e}")]
    )

    data = await request.json()
    params = None
    try:
        params = DeleteItemByIdParams(**data)
    except Exception as e:
            message = f"Error deleting Monday.com item: {e}"
            return OutputModel(
                    invocationId=invocation_id,
                    status="error",
                    response=[ResponseMessageModel(message=message)]
            )
    response = None
    try:
        response = monday_client.items.delete_item_by_id(
            item_id= params.item_id
        )
        logger.info(response)
    except Exception as e:
            message = f"Error deleting Monday.com item: {e}"
            return OutputModel(
                    invocationId=invocation_id,
                    status="error",
                    response=[ResponseMessageModel(message=message)]
            )
    if not response is None:
        logger.info("Procesa respuesta")
        message = f"Deleted item {response['data']['delete_item']['id']} Monday.com item"
    else:
        logger.info("sin respuesta")
    
    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

#monday-move-item-to-group: Moves a Monday.com item to a different group
@app.post("/monday/item/move_item_to_group")
async def move_item_to_group(request: Request) -> OutputModel:
    """Move item to another group"""
    #monday-move-item-to-group
    invocation_id = str(uuid4())
    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,
        status="error",
        response=[ResponseMessageModel(message="Connection error with Monday Client: {e}")]
    )

    data = await request.json()
    params = None
    try:
        params = MoveItemToGroupId(**data)
    except Exception as e:
        message = f"Error moving item to another group on Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                status="error",
                response=[ResponseMessageModel(message=message)]
        )
    response = None
    try:
        #llamada al servicio de monday
        response = monday_client.items.move_item_to_group(
            item_id= params.item_id,
            group_id= params.group_id
        )
        #Imprimo la respuesta
        logger.info(response)
    except Exception as e:
        message = f"Error moving item to another group on Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                status="error",
                response=[ResponseMessageModel(message=message)]
        )
    message = ""
    if not response is None:
        #Genero el mensaje de salida
        logger.info("Procesa respuesta")
        message = f"Moved item {response['data']['move_item_to_group']['id']} Monday.com item"
    else:
        logger.info("sin respuesta")

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

#El create column lo cree por curiosidad pero me da problemas al establecer el tipo de columna Actualmente no funciona
#create_column
@app.post("/monday/columns/create")
async def column_create(request: Request) -> OutputModel:
    """Create column args: board_id, column_title, column_type, defaults"""
    #Creo un identificador unico
    invocation_id = str(uuid4())
    try: 
        #Abro conexion
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        status="error",
        response=[ResponseMessageModel(message="Connection error with Monday Client: {e}")]
    )
    #Traigo losd atos del request
    data = await request.json()
    params = None
    try:
        #parseo los datos del request
        logger.info("Parse input")
        params = CreateColumn(**data)
    except Exception as e:
        message = f"Error on create column on Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                status="error",
                response=[ResponseMessageModel(message=message)]
        )
    response = None
    #llamada al servicio de monday
    #Imprimo la respuesta
    try:
        logger.info("Ejecuta api monday")
        response = monday_client.columns.create_column(
            board_id= params.board_id,
            column_title= params.column_title,
            #column_type= params.column_type
            #,#No logro identificar el valor del tipo de columna para que pueda crearla
            #column_type= 0,
            #defaults= params.defaults
        )
        logger.info(response)
    except Exception as e:
        message = f"Error on create column on Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                status="error",
                response=[ResponseMessageModel(message=message)]
        )
    message = ""
    if not response is None:
        #Genero el mensaje de salida
        logger.info("Procesa respuesta")
        #message = f"Sucessfull create column {response['data']['move_item_to_group']['id']} Monday.com item"
    else:
        logger.info("sin respuesta")

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000, log_level="info")