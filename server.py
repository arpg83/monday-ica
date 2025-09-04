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
from utils import dict_read_property,dict_read_property_into_array,dict_list_prop_id,dict_get_array

from schemas import ResponseMessageModel, OutputModel, CreateBoardParams, CreateBoardGroupParams, CreateItemParams, ListBoardsParams, GetBoardGroupsParams, UpdateItemParams, CreateUpdateCommentParams,FetchItemsByBoardId, DeleteItemByIdParams,MoveItemToGroupId,CreateColumn,GetItemComentsParams,GetItemById, ListItemsInGroupsParams, OpenExcel, ListSubitemsParams, GetBoardColumnsParams, CreateDocParams, DeleteGroupByIdParams, GetDocsParams, GetDocsContentParams

from monday import MondayClient
from monday.resources.types import BoardKind
from fastapi.responses import JSONResponse
from open_excel_utils import get_pandas

from response_classes import *

import json

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

#___________________________ Metodos pendientes ______________________________________________________________
#monday-add-doc-block: Adds a block to an existing document
#monday-archive-item: Archives a Monday.com item
#______________________________________________________________________________________________________________


#monday-list-boards: Lists all available Monday.com boards
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

#monday-list-users: Lists all available Monday.com users
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
    params = None
    monday_client = None
    try:
        params = FetchItemsByBoardId(**data)
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Conexion error with Monday Client: {e}")]
    )

    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Conexion error with Monday Client: {e}")]
    )
    try:
        board = monday_client.boards.fetch_items_by_board_id(
            board_ids= params.board_id
        )
        logger.debug(board)
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message=f"Error al llamar al servicio de Monday Client: {e}")]
    )
    #print(board["data"])

    obj_boards = Board()
    

    message = f"Informacion del Board id: {params.board_id}"
    boards = board["data"]["boards"]
    
    for board in boards:
        obj_boards.name = board["name"]
        print(obj_boards.name)
        props_bard = dict_list_prop_id(board)
        logger.debug(props_bard)
        for prop_board in props_bard:
            if prop_board == 'items_page':
                dict_items_page = board[prop_board] 
                logger.debug(dict_items_page)
                props_items_page = dict_list_prop_id(dict_items_page)
                for prop_item_page in props_items_page:
                    logger.debug(prop_item_page)
                    if prop_item_page == 'items':
                        dict_items = dict_items_page[prop_item_page]
                        groups = dict_get_array(dict_items)
                        for group in groups:
                            obj_item = Item()                            
                            logger.debug("group--")
                            logger.debug(group)
                            group_props = dict_list_prop_id(group)
                            logger.debug(group_props)
                            for group_prop in group_props:
                                if group_prop == 'id':
                                    logger.info('id')
                                    value = group[group_prop]
                                    obj_item.id = value
                                    logger.info(value)
                                if group_prop == 'name':
                                    logger.info('id')
                                    value = group[group_prop]
                                    obj_item.name = value
                                    logger.info(value)
                                if group_prop == 'group':
                                    value = group[group_prop]
                                    logger.info(group_prop)
                                    logger.info(value)
                                    #Agrego al array de grupos el grupo
                                    current_group = obj_boards.find_group_by_str(str(value),True)
                                    #Agrego item al grupo
                                    current_group.items.append(obj_item)
                                if group_prop == 'column_values':
                                    logger.debug("columnas")
                                    dict_columnas = group[group_prop]
                                    logger.debug(dict_columnas)
                                    columnas = dict_get_array(dict_columnas)
                                    for columna in columnas:
                                        obj_col = Column()
                                        obj_item.columns.append(obj_col)
                                        logger.debug(columna)
                                        columna_props = dict_list_prop_id(columna)
                                        for columna_prop in columna_props:
                                            logger.debug(columna_prop)
                                            if columna_prop == 'id':
                                                value = columna[columna_prop]
                                                logger.info(value)
                                                obj_col.id = value
                                            if columna_prop == 'text':
                                                value = columna[columna_prop]
                                                logger.info(value)
                                                obj_col.text = value
                                            if columna_prop == 'type':
                                                value = columna[columna_prop]
                                                logger.info(value)
                                                obj_col.type = value
                                            if columna_prop == 'status':
                                                value = columna[columna_prop]
                                                logger.info(value)
                                                obj_col.status = value
                                            if columna_prop == 'value':
                                                dict_values = columna[columna_prop]
                                                logger.debug(columna_prop)
                                                logger.debug(dict_values)
                                                obj_col.value = str(dict_values)
                                                message = f"{message}  {columna_prop}: {columna[columna_prop]}"    
                                                #values = dict_list_prop_id(dict_values)
                                                #logger.info(values)
                                                #for value in values:
                                                    #logger.info(value)
                                                    #cols_id_value = dict_list_prop_id(value)
                                                    #logger.info(cols_id_value)
                                                #for col_id_value in cols_id_value:    
                                                #    message = f"{message}  {col_id_value}: {values[col_id_value]}"    
                                            else:
                                                logger.debug(columna[columna_prop])
                                                message = f"{message}  {columna_prop}: {columna[columna_prop]}"    
                                elif group_prop == 'group':
                                    logger.debug(group_prop)
                                    #logger.info(group[group_prop])
                                    desc_props = group[group_prop]
                                    group_desc_props = dict_list_prop_id(desc_props)
                                    for group_desc_prop in group_desc_props:
                                        message = f"{message}  {group_desc_prop}: {desc_props[group_desc_prop]}"
                                else:
                                    logger.debug(group_prop)
                                    logger.debug(group[group_prop])
                                    message = f"{message}  {group_prop}: {group[group_prop]}"

                    else:
                        message = f"{message}  {prop_item_page}: {dict_items_page[prop_item_page]}"

            else:
                message = f"{message}  {prop_board}: {board[prop_board]}"

    
    template = template_env.get_template("response_template_fetch_items_by_board_id.jinja")
    message = template.render(
        obj_boards= obj_boards
    )
    logger.info(message)

#        logger.info(board)
#        logger.info(board_name)
#        message = f"{message}  Board: {board_name}"
#        items_page = board["items_page"]
#        if "cursor" in items_page:
#            cursor = items_page["cursor"]
#            message = f"{message}  Cursor: {cursor}"
#            items = items_page["items"]
#            for item in items:
#                group = item["group"]
#                column_values = item["column_values"]
#                id = item["id"]
#                name = item["name"]
#                logger.info(name)
#                message = f"{message}  item name: {name}"
#                message = f"{message}  id: {id}"
#                if "column_values" in item:
#                    column_values = item["column_values"]
#                    for column in column_values:
#                        col_id = column["id"]
#                        text = column["text"]
#                        message = f"{message}  Column id: {col_id}"
#                        message = f"{message}  Column text: {text}"

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
    )

#------------------REVISAR-----------------------------------------
#    message = "Épicas"
#    content = {"message":message}
#    headers = {'Content-Disposition': 'inline; filename="out.json"'}

#    return JSONResponse(
#        content=content,
#        headers=headers
#    )
#-----------------------------------------------------------------

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
                column_values=params.column_values,
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
                column_values=params.column_values
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
            column_values=params.column_values
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
@app.delete("/monday/item/delete")
async def delete_item_by_id(request: Request) -> OutputModel:
    """Delete item by id args item_id"""
    invocation_id = str(uuid4())
    monday_client = None
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
    if not response == None:
        deleted_item = response['data']['delete_item']['id']

        template = template_env.get_template("response_template_item_delete.jinja")
        message = template.render(
            deleted_item = deleted_item
        )
    
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
    monday_client = None
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

#monday-get-item-updates: Retrieves updates/comments for a specific item
@app.post("/monday/item/get_item_updates")
async def get_item_updates(request: Request) -> OutputModel:
    """Retrieves updates/comments for a specific item"""
    #monday-move-item-to-group
    #genera id unico
    invocation_id = str(uuid4())
    monday_client = None
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
        params = GetItemComentsParams(**data)
        logger.info(params)
    except Exception as e:
        message = f"Error get item on Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                status="error",
                response=[ResponseMessageModel(message=message)]
        )
    response = None
    try:
        #llamada al servicio de monday
        response = monday_client.updates.fetch_updates_for_item(
            item_id=params.item_id,
            limit=params.limit
        )
        #Imprimo la respuesta
        logger.debug(response)
    except Exception as e:
        message = f"Error  get item on Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                status="error",
                response=[ResponseMessageModel(message=message)]
        )
    message = ""
    if not response is None:
        #Genero el mensaje de salida
        logger.info("Procesa respuesta")
        logger.info(response)
        message = "item updates: "
        items = response['data']['items']
        for item in items:
            logger.debug(item['updates'])
            updates = item['updates']
            for update in dict_get_array(updates):
                logger.debug(update)
                for prop_id in dict_list_prop_id(update):
                    logger.debug(prop_id)
                    if prop_id == 'creator':
                        creator = update[prop_id]
                        props_id_b = dict_list_prop_id(creator)
                        logger.debug(props_id_b)
                        for prop_id_b in props_id_b:
                            message = f"{message} {prop_id_b}: {creator[prop_id_b]}"
                    else:
                        message = f"{message} {prop_id}: {update[prop_id]}"

        message = f"{message} Monday.com"
    else:
        logger.info("sin respuesta")

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

#monday-get-item-by-id: Retrieves items by theirs IDs
@app.post("/monday/item/get_item_by_id")
async def get_item_by_id(request: Request) -> OutputModel:
    """Fetch specific Monday.com items by their IDs"""
    
    #------------------REVISAR--------------------------------------
    #"""Retrieves updates/comments for a specific item"""
    ##monday-move-item-to-group
    #----------------------------------------------------------------

    #genera id unico
    invocation_id = str(uuid4())
    monday_client = None
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
        params = GetItemById(**data)
        logger.debug(params)
    except Exception as e:
        message = f"Error get item on Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                status="error",
                response=[ResponseMessageModel(message=message)]
        )
    response = None
    try:
        #llamada al servicio de monday
        response = monday_client.items.fetch_items_by_id(
            ids = params.items_id
        )
        #Imprimo la respuesta
        logger.debug(response)
    except Exception as e:
        message = f"Error  get item on Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                status="error",
                response=[ResponseMessageModel(message=message)]
        )
    message = ""
    if not response is None:
        #Genero el mensaje de salida
        #logger.debug("Procesa respuesta")
        data = dict_read_property(response,'data')
        #logger.debug(data)
        items = dict_read_property(data,'items')
        #logger.debug(dict_read_property_into_array(items,'id'))
        #logger.debug(dict_read_property_into_array(items,'name'))
        columns = dict_read_property_into_array(items,'column_values')
        #logger.info(columns)
        arr_cols = dict_get_array(columns)
        #logger.info(dict_read_property_into_array(columns,'id'))
        message = f"Get item id {dict_read_property_into_array(items,'id')} item name: {dict_read_property_into_array(items,'name')}"
        for item_arr in arr_cols:
            logger.info(item_arr)
            message = f"{message} Column: "
            for prop_id in dict_list_prop_id(item_arr):
                logger.info(prop_id)
                message = f"{message} {prop_id}: {dict_read_property(item_arr,prop_id)}"

        message = f"{message} Monday.com item"
    else:
        logger.debug("sin respuesta")

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

#----------------REVISAR-------------------------------------------------
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
        logger.debug(response)
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
    params = None 
    message = "" 

    try:
        params = GetBoardGroupsParams(**data)
    except Exception as e:
        message = f"Error Getting groups of the Monday.com Board: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    
    response = None
    message = ""
    
    try:
        #llamada al servicio de monday
        response = monday_client.groups.get_groups_by_board(board_ids=params.board_id)

        #Imprimo la respuesta
        logger.info(response)

    except Exception as e:
        message = f"Error Getting groups of the Monday.com Board: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    
    message = ""
    if not response is None:
        #Genero el mensaje de salida
        logger.info("Procesa respuesta")        
       
        message = f"Available Monday.com Groups: \n %s" % (response['data']) 

    else:
        logger.info("sin respuesta")

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        ) 

#monday-create-board-group: Creates a new group in a Monday.com board    
@app.post("/monday/board_group/create")
async def create_board_group(request: Request) -> OutputModel:
    """Create a new group in a Monday.com board.

    Args:
        boardId: Monday.com Board ID that the group will be created in.
        groupName: Name of the group to create.
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
    message = "" 

    try:
        params = CreateBoardGroupParams(**data)
    except Exception as e:
        message = f"Error Creating a group on a Monday.com Board: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    
    response = None
    message = ""
    
    try:
        #llamada al servicio de monday
        response = monday_client.groups.create_group(board_id=params.board_id, group_name=params.group_name)

        #Imprimo la respuesta
        logger.info(response)
    except Exception as e:
        message = f"Error Creating a Monday.com Group: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    
    message = ""
    if not response is None:
        #Genero el mensaje de salida
        logger.info("Procesa respuesta")  
        
        message = f"Created new group: {params.group_name} in board: {params.board_id}. ID of the group: {response['data']['create_group']['id']}"
    else:
        logger.info("sin respuesta")

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        ) 
     
#monday-list-items-in-groups: Lists all items in specified groups of a Monday.com board
@app.post("/monday/item_in_group/list")
async def list_items_in_groups(request: Request) -> OutputModel:
    """
    List all items in the specified groups of a Monday.com board.
    """
    invocation_id = str(uuid4())

    try:
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Conexión error con Monday Client: {e}")]
        )

    try:
        data = await request.json()
        params = ListItemsInGroupsParams(**data)
    except Exception as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error en parámetros: {e}")]
        )

    # Construimos la lista de IDs de grupos para GraphQL
    formatted_group_ids = ", ".join([f'"{gid}"' for gid in params.group_ids])

    # Query GraphQL para traer items por grupo
    query = f"""
    query {{
      boards (ids: {params.board_id}) {{
        groups (ids: [{formatted_group_ids}]) {{
          id
          title
          items_page (limit: {params.limit}) {{
            items {{
              id
              name
            }}
          }}
        }}
      }}
    }}
    """

    try:
        response = monday_client.custom._query(query)
        logger.info(response)
    except requests.RequestException as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error consultando Monday.com: {e}")]
        )

    # Procesar respuesta
    items = []
    try:
        groups_data = response.get("data", {}).get("boards", [])[0].get("groups", [])
        for group in groups_data:
            group_name = group.get("title", "Sin nombre")
            for item in group.get("items_page", {}).get("items", []):
                items.append(f"- {item['name']} (ID: {item['id']}) en grupo {group_name}")
    except Exception as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error procesando respuesta: {e}")]
        )


    if not items:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message="No se encontraron ítems en los grupos especificados.")]
        )

    message = f"Items en los grupos {params.group_ids} del board {params.board_id}:\\n" + "\\n".join(items)

    return OutputModel(
        invocationId=invocation_id,
        response=[ResponseMessageModel(message=message)]
    )

#monday-list-subitems-in-items: Lists all sub-items for given Monday.com items
@app.post("/monday/subitem_in_item/list")
async def list_subitems_in_items(request: Request) -> OutputModel:
    """
    Lists all sub-items for given Monday.com items.
    """
    invocation_id = str(uuid4())

    try:
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Conexión error con Monday Client: {e}")]
        )

    try:
        data = await request.json()
        params = ListSubitemsParams(**data)
    except Exception as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error en parámetros: {e}")]
        )

    # Construimos la lista de IDs de items para GraphQL
    formatted_item_ids = ", ".join([f'"{gid}"' for gid in params.item_ids])

    # Query GraphQL para traer subitems por item
    query = f"""
    query {{
    items (ids: [{formatted_item_ids}]) {{
        id
        name
        subitems {{
        id
        name
        }}
    }}
    }}
    """

    try:
        response = monday_client.custom._query(query)
        logger.info(response)
    except requests.RequestException as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error consultando Monday.com: {e}")]
        )

    # Procesar respuesta
    subitems = []
    try:
        items_data = response.get("data", {}).get("items", [])
        for item in items_data:
            for sub in item.get("subitems", []):
                subitems.append(f"- {sub['name']} (ID: {sub['id']})")
    except Exception as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error procesando respuesta: {e}")]
        )

    if not subitems:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message="No se encontraron subítems en los items especificados.")]
        )

    message = f"Subitems en los Items {params.item_ids} :\\n" + "\\n".join(subitems)

    return OutputModel(
        invocationId=invocation_id,
        response=[ResponseMessageModel(message=message)]
    )

#monday-open_excel: -----------COMPLETAR-----------------
@app.post("/monday/read_excel")
async def open_excel(request: Request) -> OutputModel:

    #------------------REVISAR--------------------------------------
    # Completar comentarios....que hace, que recibe, que devuelve....
    #---------------------------------------------------------------
    
    invocation_id = str(uuid4())
    
    data = await request.json()
    params = None
    try:
        #parseo los datos del request
        logger.info("Parse input")
        params = OpenExcel(**data)
    except Exception as e:
        message = f"Error on create column on Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                status="error",
                response=[ResponseMessageModel(message=message)]
        )
    #path = "C:/$user/Agentes IA/TestExcel/destino.xlsx"
    df = get_pandas(params.file_name,params.download)
    #desde aca se encontraria el codigo para procesar los datos del pandas dataframe
    #Mensaje de retorno

    message = ""

    return OutputModel(
        invocationId=invocation_id,
        response=[ResponseMessageModel(message=message)]
    )

#monday-get-board-columns: Get the Columns of a Monday.com Board
@app.post("/monday/columns/get")
async def get_board_columns(request: Request) -> OutputModel:
    """Get the Columns of a Monday.com Board.

        Args:
            boardId: Monday.com Board ID that the Item or Sub-item is on.
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
    message = "" 

    try:
        params = GetBoardColumnsParams(**data)
    except Exception as e:
        message = f"Error Getting Columns of the Monday.com Board: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    
    response = None
    message = ""
           
    query = f"""
        query {{
            boards(ids: {params.board_id}) {{
                columns {{
                    id
                    title
                    type
                    settings_str
                }}
            }}
        }}
    """     

    #Llamada al servicio de Monday
    response = monday_client.custom._query(query)

    #Imprime la respuesta
    logger.info(response)


    for board in response.get("data", {}).get("boards", []):
            for column in board["columns"]:
                settings_str = column.pop("settings_str", None)
                if settings_str:
                    if isinstance(settings_str, str):
                        try:
                            settings_obj = json.loads(settings_str)
                            if settings_obj.get("labels"):
                                column["available_labels"] = settings_obj["labels"]
                        except json.JSONDecodeError:
                            pass
            
    message = ""
    if not response is None:
        #Genera el mensaje de salida
        logger.info("Procesa respuesta")        
       
        message = f"Available Monday.com Columns: \n %s" % (response['data']) 

    else:
        logger.info("sin respuesta")

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        ) 

#monday-delete-group: Deletes a Monday.com group
@app.delete("/monday/group/delete")
async def delete_group_by_id(request: Request) -> OutputModel:
    """Delete group by id args group_id"""
    invocation_id = str(uuid4())
    monday_client = None
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
        params = DeleteGroupByIdParams(**data)
    except Exception as e:
            message = f"Error deleting Monday.com item: {e}"
            return OutputModel(
                    invocationId=invocation_id,
                    status="error",
                    response=[ResponseMessageModel(message=message)]
            )
    response = None
    try:
        response = monday_client.groups.delete_group(
            board_id = params.board_id,
            group_id = params.group_id
        )
        logger.info(response)
    except Exception as e:
            message = f"Error deleting Monday.com group: {e}"
            return OutputModel(
                    invocationId=invocation_id,
                    status="error",
                    response=[ResponseMessageModel(message=message)]
            )
    


    if not response is None:
        logger.info("Procesa respuesta")
        message = f"Deleted group {response['data']['delete_group']['id']} Monday.com group"
    else:
        logger.info("sin respuesta")
    
    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

#monday-get-docs: Lists documents in Monday.com, optionally filtered by folder 
@app.post("/monday/docs/list")
async def get_docs(request: Request) -> OutputModel:
        """
        Get a list of documents.

        Args:
            limit (int): Max number of documents to fetch

        Returns:
            str: Human-readable list of documents
        """

        invocation_id = str(uuid4())
        logger.info(invocation_id)
     
        try:
            monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
        except requests.RequestException as e:
            return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=f"Connection error with Monday Client: {e}")]
            )            
        
        try:
            data = await request.json()
            params = GetDocsParams(**data)
            logger.info(params)
        except Exception as e:
                message = f"Error getting Monday.com docs: {e}"
                logger.info("Error with params")
                return OutputModel(
                        invocationId=invocation_id,
                        status="error",
                        response=[ResponseMessageModel(message=message)]
                )
        response = None        

        # Query GraphQL para traer los docs
        query = f"""
        query {{
            docs (limit: {params.limit}) {{
                id
                name
                created_at
                workspace_id
                doc_folder_id
                created_by {{
                    id
                    name
                }}
            }}
        }}
        """
        
        try:
            response = monday_client.custom._query(query)
            logger.info(response)
        except requests.RequestException as e:
           logger.info("sin respuesta")
           return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=f"Error consulting docs in Monday.com: {e}")]               
            )
              
        try:
            docs = (response or {}).get("data", {}).get("docs", [])
            logger.info(docs)
        except Exception as e:
            logger.info("error en el try de docs")
            return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error processing response: {e}")]            
        )
    
        if not docs:
            return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message="No documents found.")]
            )
        
        # Procesar respuesta
        lines = []
        for d in docs:
            lines.append(
                f"Document ID: {d['id']}\n"
                f"Name: {d['name']}\n"
                f"Created: {d['created_at']}\n"
                f"Workspace ID: {d['workspace_id']}\n"
                f"Folder ID: {d.get('doc_folder_id','None')}\n"
                f"Created by: {d['created_by']['name']} (ID: {d['created_by']['id']})\n"
                "-----\n"
            )
        
        message = f"Documents:\n\n" + "\n".join(lines)

        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

#monday-get-doc-content: Retrieves the content of a specific document
@app.post("/monday/doc_content/get")
async def get_doc_content(request: Request) -> OutputModel:
        """
        Get the content blocks of a document.

        Args:
            doc_id (str): Document ID

        Returns:
            str: Document content listing
        """
        invocation_id = str(uuid4())
        logger.info(invocation_id)

        try:
            monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
        except requests.RequestException as e:
            return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Connection error with Monday Client: {e}")]
        )
                
        params = None

        try:
            data = await request.json()
            params = GetDocsContentParams(**data)
            logger.info(params)
        except Exception as e:
            message = f"Error getting Monday.com doc_content: {e}"
            logger.info("Error with params")
            return OutputModel(
                    invocationId=invocation_id,
                    status="error",
                    response=[ResponseMessageModel(message=message)]
            )
        
        response = None

         # Query GraphQL para traer los docs        
        query = f"""
        query {{
            docs (ids: {params.doc_id}) {{
                id
                name
                blocks {{
                    id
                    type
                    content
                }}
            }}
        }}
        """
        try:
            response = monday_client.custom._query(query)
            logger.info(response)
        except requests.RequestException as e:
           logger.info("sin respuesta")
           return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=f"Error consulting doc_content in Monday.com: {e}")]               
            )

        try:
            docs = (response or {}).get("data", {}).get("docs", [])
            logger.info(docs)
        except Exception as e:
            logger.info("error en el try de docs")
            return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error processing response: {e}")]            
        )
    
        if not docs:

            message = f"Document with ID {params.doc_id} not found."
            return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
            )
        
        doc = docs[0]
        
        try:
            blocks = doc.get("blocks", [])
            logger.info(blocks)
        except Exception as e:
            logger.info("error en el try de blocks")
            return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error processing response: {e}")]            
        )       
           
        if not blocks:
            message = f"Document {doc['name']} (ID: {doc['id']}) has no content blocks."            
            return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
            )

         # Procesar respuesta 
        lines = [f"Document {doc['name']} (ID: {doc['id']}):\n\nBlocks:"]
        for b in blocks:
            lines.append(f"- Block ID: {b['id']} | Type: {b['type']} | Content: {b['content']}")

        message = f"Documents:\n\n" + "\n".join(lines)

        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

#___________________________ Myrian Workspace ______________________________________________________________

''' CREATE DOC-----------------------------------------------
#monday-create-doc: Creates a new document in Monday.com
@app.post("/monday/doc/create")
async def Create_doc(request: Request) -> OutputModel:
    """
        Create a new document.

        Args:
            title (str): Document title
            workspace_id (Optional[int]): Workspace ID (requires 'kind')
            board_id (Optional[int]): Board ID (requires column_id & item_id)
            kind (Optional[str]): Kind of workspace doc
            column_id (Optional[str]): Column ID (when board_id is used)
            item_id (Optional[int]): Item ID (when board_id is used)

        Returns:
            str: Confirmation message with doc URL or error
     """

    invocation_id = str(uuid4())

    try:
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Connection error with Monday Client: {e}")]
        )
                
    params = None

    try:
        data = await request.json()
        params = CreateDocParams(**data)
    except Exception as e:
            message = f"Error deleting Monday.com item: {e}"
            return OutputModel(
                    invocationId=invocation_id,
                    status="error",
                    response=[ResponseMessageModel(message=message)]
            )
    response = None

    if params.workspace_id:
            if not params.kind:
                return "'kind' is required when using workspace_id."
            location = f'location: {{workspace: {{ workspace_id: {params.workspace_id}, name: "{params.title}", kind: {params.kind} }} }}'
    elif params.board_id:
            if not params.column_id or not params.item_id:
                return "'column_id' and 'item_id' are required when using board_id."
            location = f'location: {{board: {{ board_id: {params.board_id}, column_id: "{params.column_id}", item_id: {params.item_id} }} }}'
    else:
            return "You must provide either workspace_id or board_id."

    mutation = f"""
        mutation {{
            create_doc (
                {location}
            ) {{
                id
            }}
        }}
        """
    response = monday_client.custom._query(mutation)
    created = (response or {}).get("data", {}).get("create_doc")
    if not created:
            return "Failed to create document."

    doc_id = created["id"]
    try:
            monday_url = os.getenv("MONDAY_WORKSPACE_URL")
            doc_url = f"{monday_url}/docs/{doc_id}"
    except NameError:
            doc_url = f"(workspace URL not configured) Doc ID {doc_id}"

    return f"Document created successfully!\nTitle: {params.title}\nID: {doc_id}\nURL: {doc_url}"
'''
   
#___________________________________________________________________________________________________________

#___________________________ Luciano Workspace ______________________________________________________________
#___________________________________________________________________________________________________________

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000, log_level="info")