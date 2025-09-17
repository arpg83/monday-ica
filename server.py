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

from schemas import ResponseMessageModel, OutputModel, CreateBoardParams, CreateBoardGroupParams, CreateItemParams, ListBoardsParams, GetBoardGroupsParams, UpdateItemParams, CreateUpdateCommentParams,FetchItemsByBoardId, DeleteItemByIdParams,MoveItemToGroup,GetItemUpdatesParams,GetItemByIdParams, ListItemsInGroupsParams, OpenExcel, ListSubitemsParams, GetBoardColumnsParams, CreateDocParams, DeleteGroupByIdParams, ArchiveItemParams, GetDocsParams, GetDocContentParams, AddDocBlockParams, CreateColumnParams

from monday import MondayClient
from monday.resources.types import BoardKind
from fastapi.responses import JSONResponse
from open_excel_utils import *

from response_classes import *

import json
from threading import Thread

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

#______________________________________________________________________________________________________________
#___________________________ CREATE____________________________________________________________________________
#______________________________________________________________________________________________________________

# 1 - monday-create-board: Creates a new Monday.com board
@app.post("/monday/board/create")
async def create_board(request: Request) -> OutputModel:
    """
    Crea un nuevo tablero en Monday.com

    Parámetros de entrada:
        board_name (str): El nombre del tablero.
        board_kind (str): La clase de tablro a crear. Debe ser "publico" o "privado".

    Retorna:
        board_id: ID del tablero creado
    """
    invocation_id = str(uuid4())
    data = await request.json()
    params = CreateBoardParams(**data)

    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Error de conexión con el cliente de Monday: {e}")]
    )

    actual_board_kind = BoardKind(params.board_kind)
    board = monday_client.boards.create_board(
    board_name=params.board_name, board_kind=actual_board_kind
    )

    #message = f"Created monday board {params.board_name} of kind {params.board_kind}. ID of the new board: {board['data']['create_board']['id']}"
    
    template = template_env.get_template("response_template_board_created.jinja")
    message = template.render(
        board_name = params.board_name,
        board_kind = params.board_kind,
        board_id = board['data']['create_board']['id']
    )

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
    )
 
# 2 - monday-create-board-group: Creates a new group in a Monday.com board  
@app.post("/monday/board_group/create")
async def create_board_group(request: Request) -> OutputModel:
    """Crea un nuevo grupo en un tablero de Monday.com

    Parámetros de entrada:
        boardId: Id del tablero donde se creará el nuevo grupo.
        groupName: Nombre del grupo que se creará.

    Retorna:
        group_id: ID del grupo creado.    
    """
    invocation_id = str(uuid4())

    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Error de conexión con el cliente de Monday: {e}")]
    )

    data = await request.json()
    params = None 
    message = "" 

    try:
        params = CreateBoardGroupParams(**data)
    except Exception as e:
        message = f"Error al recuperar los parámetros, verificar que el ID del tablero exista en Monday.com: {e}"
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
        message = f"Error de respuesta al solicitar la creación del grupo en Monday.com:{e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    
    message = ""
    if not response is None:
        #Genero el mensaje de salida
        logger.info("Procesa respuesta")  
        
    #    message = f"Created new group: {params.group_name} in board: {params.board_id}. ID of the group: {response['data']['create_group']['id']}"
    
        template = template_env.get_template("response_template_group_board_created.jinja")
        message = template.render(
            board_id = params.board_id,
            group_name = params.group_name,
            group_id = response['data']['create_group']['id']
        )
    
    else:
        logger.info("sin respuesta")

        message = f"No se pudo crear el grupo en Monday.com."

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        ) 
    
# 3 - monday-create-item: Creates a new item or sub-item in a Monday.com board
@app.post("/monday/item/create")
async def create_item(request: Request) -> OutputModel:
    """
    Crea una tarea nueva en un tablero de Monday.com. 
    Opcionalmente, podra especificarse el ID de una tarea padre para crear un subitem.

    Parámetros de entrada:
        item_name: Nombre de la tarea o subtarea
        board_id: Id del tablero donde se creará la nueva tarea. (Opcional)
        group_id: Id del grupo donde se creará la nueva tarea.(Opcional)
        parent_item_id: Id de la tarea donde se creará la subtarea.(Opcional)
        column_values: Nombres de las columnas asociadas a la tarea que se creará.(Opcional)

    Devuelve:
        Detalle incluyendo el ID de la tarea creada.
    """
    invocation_id = str(uuid4())
    data = await request.json()
    
    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Error de conexión con el cliente de Monday: {e}")]
    )

    message = ""
    response = None
    params = None

    try:
        params = CreateItemParams(**data)
    except Exception as e:
        message = f"Error al recuperar los parámetros, verificar que el o los IDs proporcionados existan en Monday.com: {e}"
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

            message = f"Error al crear una tarea en Monday.com: {e}"

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

            message = f"Error al crear una subtarea en Monday.com: {e}"

            return OutputModel(
                    invocationId=invocation_id,
                    response=[ResponseMessageModel(message=message)]
            )
    else:
        message = f"Puede ingresar el ID de grupo o el ID de una tarea, pero no ambos."
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
            #message = f"Se creó una nueva tarea en Monday.com: {params.item_name} en el tablero cuyo ID es: : {params.board_id} and group Id: {params.group_id}."   
            logger.info(response['data']['create_item']['id'])
            template = template_env.get_template("response_template_item_created.jinja")
            message = template.render(
                item_name = params.item_name,
                board_id = params.board_id,
                group_id = params.group_id,
                item_id = response['data']['create_item']['id'],
                flag_tipo = "item",
                Columns_values = params.column_values
                )
        elif params.parent_item_id is not None and params.group_id is None:
        #elif "parent_item_id" in data:
             #message = f"Created a new Monday.com sub item: {params.parent_item_id} en el tablero cuyo ID es: : {params.board_id}."
            logger.info(response)
            subitemid = response['data']['create_subitem']['id']
            template = template_env.get_template("response_template_item_created.jinja")
            message = template.render(
                item_name = params.item_name,
                parent_item_id = params.parent_item_id,
                flag_tipo = "subitem",
                Columns_values = params.column_values,
                item_id = subitemid
                )       
        else:
            message = f"Se creó una nueva tarea en Monday.com: {params.item_name} en el tablero cuyo ID es: : {params.board_id}."

        return OutputModel(
                    invocationId=invocation_id,
                    response=[ResponseMessageModel(message=message)]
        )
    
    except Exception as e:

            message = f"No se pudo crear una tarea o subtarea en Monday.com: {e}"

            return OutputModel(
                    invocationId=invocation_id,
                    response=[ResponseMessageModel(message=message)]
            )

# 4 - monday-create-update: Creates a comment/update on a Monday.com item
@app.put("/monday/comment/update")
async def create_update_comment(request: Request) -> OutputModel:    
    """
     Crea una actualización (comentario) sobre una tarea o subtarea de Monday.com

    Parámetros de entrada:
        item_id: (str) ID de la tarea que se actualizará
        update_text: (str) Texto que se desea incluir en la tarea

    Retorna:
        Detalle de la tarea actualizada.
     """
    invocation_id = str(uuid4())

    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Error de conexión con el cliente de Monday: {e}")]
    )

    data = await request.json()
    params = None  

    try:
        params = CreateUpdateCommentParams(**data)
    except Exception as e:
        message = f"Error al recuperar los parámetros, verificar que el ID de la tarea exista en Monday.com: {e}"
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
        message = f"Error de respuesta al solicitar la creación de la actualización (comentario) de una tarea o subtares en Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    message = ""
    if not response is None:
        #Genero el mensaje de salida
        logger.info("Procesa respuesta")        
        message = f"Se creó una nueva actualización (comentario) en la tarea o subtarea especificada en Monday.com: {response['data']['create_update']['id']}"
    else:
        logger.info("sin respuesta")
    
    message = f"No se pudo crear la nueva actualización (comentario) en la tarea o subtarea especificada en Monday.com."
    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

# 5 - monday-create-doc: Creates a new document in Monday.com
@app.post("/monday/doc/create")
async def create_doc(request: Request) -> OutputModel:
    """
        Crea un nuevo documento en Monday.com

        Parámetros de entrada:
            title (str): Titulo del documento.
            workspace_id (Opcional[int]): ID del espacio de trabajo (requiere el tipo de documento ('kind'))
            board_id (Opcional[int]): ID del tablero (requiere ID de la columna (column_id) y ID de la tarea (item_id))
            kind (Opcional[str]): Tipo de documento del espacio de trabajo
            column_id (Opcional[str]): ID de la columna (cuando se utiliza un tablero (board_id))
            item_id (Opcional[int]): ID de la tarea (cuando se utiliza un tablero (board_id)

        Retorna:
            str: Mensajde confirmación con la URL del documento creado o con el error si la creación falló.
     """

    invocation_id = str(uuid4())
    logger.info(invocation_id)

    try:
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error de conexión con el cliente de Monday: {e}")]
        )
                
    params = None

    try:
        data = await request.json()
        params = CreateDocParams(**data)
        logger.info(params)
    except Exception as e:
            message = f"Error al recuperar los parámetros, verificar que el ID del espacio de trabajo o el ID del tablero proporcionado, exista en Monday.com: {e}"
            return OutputModel(
                    invocationId=invocation_id,
                    status="error",
                    response=[ResponseMessageModel(message=message)]
            )
    
    if params.workspace_id:
            if not params.kind:
                message = "'kind' es requerido cuando se utiliza el ID del espacio de trabajo."
            location = f'location: {{workspace: {{ workspace_id: {params.workspace_id}, name: "{params.title}", kind: {params.kind} }} }}'
    elif params.board_id:
            if not params.column_id or not params.item_id:
                message =  "'column_id' and 'item_id' are required when using board_id."
            location = f'location: {{board: {{ board_id: {params.board_id}, column_id: "{params.column_id}", item_id: {params.item_id} }} }}'
    else:
            message =  "Puede ingresar el ID del Espacio de trabajo o el ID del Tablero."
            logger.info(location)
            return OutputModel(
                    invocationId=invocation_id,
                    status="error",
                    response=[ResponseMessageModel(message=message)]
            )    
    
    mutation = f"""
        mutation {{
            create_doc (
                {location}
            ) {{
                id
            }}
        }}
        """
    
    response = None
    
    try:
        response = monday_client.custom._query(mutation)
        logger.info(response)
    except requests.RequestException as e:
           logger.info("sin respuesta")
           return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=f"Error de respuesta al solicitar la creación del documento en Monday.com: {e}")]               
            )

    try:
            created = (response or {}).get("data", {}).get("create_doc")
            logger.info(created)
    except Exception as e:
            logger.info("error en el try de created")
            return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error al procesar la respuesta de Monday.com: {e}")]            
        )

    if not created:
            message = "No se pudo crear el documento en Monday.com."
            return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
            )    
       
     # Procesar respuesta 

    try:
        monday_workspace_name = MondayClient(os.getenv("MONDAY_WORKSPACE_NAME"))
    except requests.RequestException as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error de conexión con el cliente de Monday: {e}")]
        )
    
    doc_id = created["id"]
    try:
            monday_url = os.getenv("MONDAY_WORKSPACE_URL")
            doc_url = f"{monday_url}/docs/{doc_id}"
    except NameError:
            doc_url = f"(La URL del Espacio de trabajo no está configurada) Doc ID {doc_id}"

    message = f"El documento fue creado exitosamente!\nTitulo: {params.title}\nID del documento: {doc_id}\nURL: {doc_url}"

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )
   

#______________________________________________________________________________________________________________
#___________________________ LIST______________________________________________________________________________
#______________________________________________________________________________________________________________

# 6 - monday-list-boards: Lists all Tableros disponibles en Monday.com
@app.post("/monday/boards/list")
async def listBoards(request: Request) -> OutputModel:    
    """
    Lista los tableros disponibles en Monday.com

    Parámetros de entrada:
        limit: Cantidad de tableros a listar por página
        page: Número de página
        
    Retorna:
        Lista de tableros disponibles en Monday.com
    """
    invocation_id = str(uuid4())
    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Error de conexión con el cliente de Monday: {e}")]
    )

    data = await request.json()
    params = ListBoardsParams(**data)
    response = monday_client.boards.fetch_boards(limit=params.limit, page=params.page)
    boards = response["data"]["boards"]
    board_list = "\n".join(
        [f"- {board['name']} (ID: {board['id']})" for board in boards]
    )
    message = "Tableros disponibles en Monday.com: \n %s" % (board_list) 

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
    )

# 7 - monday-get-board-groups: Retrieves all groups from a specified Monday.com board
@app.get("/monday/board_groups/get")
async def getBoardGroups(request: Request) -> OutputModel:
    """
    Lista los grupos de un tablero de Monday.com

    Parámetros de entrada: 
        board_id: ID del tablero de Monday.com
        
    Retorna:
        Lista de los grupos disponibles para el tablero especificado.
        
    """
    invocation_id = str(uuid4())

    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Error de conexión con el cliente de Monday: {e}")]
    )

    data = await request.json()
    params = None 
    message = "" 

    try:
        params = GetBoardGroupsParams(**data)
    except Exception as e:
        message = f"Error al recuperar los parámetros, verificar que el ID del tablero exista en Monday.com: {e}"
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
        message = f"Error de respuesta al solicitar la lista de grupos del tablero especificado en Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    
    message = ""
    if not response is None:
        #Genero el mensaje de salida
        logger.info("Procesa respuesta")        
       
        message = f"Grupos disponibles en un tablero especificado de Monday.com: \n %s" % (response['data']) 

    else:
        logger.info("sin respuesta")
        message = "Error de respuesta al solicitar la lista de grupos que posee el tablero especificados en Monday.com:"

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        ) 
        
# 8 - monday-list-items-in-groups: Lists all items in specified groups of a Monday.com board
@app.post("/monday/item_in_group/list")
async def list_items_in_groups(request: Request) -> OutputModel:
    """
    Lista todas las tareas y subtareas en los grupos contenidos en un tablero de Monday.com.
    """
    invocation_id = str(uuid4())

    try:
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error de conexión con el cliente de Monday: {e}")]
        )

    try:
        data = await request.json()
        params = ListItemsInGroupsParams(**data)
    except Exception as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error al recuperar los parámetros, verificar que el ID del tablero o los IDs de los grupos, existan en Monday.com: {e}")]
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
            response=[ResponseMessageModel(message=f"Error de respuesta al solicitar la lista de tareas de los grupos, de un tablero de Monday.com: {e}")]
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
            response=[ResponseMessageModel(message=f"Error al procesar la respuesta de Monday.com: {e}")]
        )


    if not items:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"No se encontraron ítems en los grupos especificados.")]
        )

    message = f"IDs de los grupos: {params.group_ids} ID del tablero: {params.board_id} Tareas: \\n" + "\\n".join(items)

    return OutputModel(
        invocationId=invocation_id,
        response=[ResponseMessageModel(message=message)]
    )

# 9 - monday-list-subitems-in-items: Lists all sub-items for given Monday.com items
@app.post("/monday/subitem_in_item/list")
async def list_subitems_in_items(request: Request) -> OutputModel:
    """
    Lista todas las subtareas contenidas en una tarea de Monday.com.
    """
    invocation_id = str(uuid4())

    try:
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error de conexión con el cliente de Monday: {e}")]
        )

    try:
        data = await request.json()
        params = ListSubitemsParams(**data)
    except Exception as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error al recuperar los parámetros, verificar que los IDs de las tareas existan en Monday.com: {e}")]
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
            response=[ResponseMessageModel(message=f"Error de respuesta al solicitar la lista de subtareas de tareas especificadas en Monday.com: {e}")]
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
            response=[ResponseMessageModel(message=f"Error al procesar la respuesta de Monday.com: {e}")]
        )

    if not subitems:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message="No se encontraron subtareas en las tareas especificadas.")]
        )

    message = f"Subtareas en las Tareas {params.item_ids} :\\n" + "\\n".join(subitems)

    return OutputModel(
        invocationId=invocation_id,
        response=[ResponseMessageModel(message=message)]
    )

# 10 - monday-get-item-updates: Retrieves updates/comments for a specific item
@app.post("/monday/item/get_item_updates")
async def get_item_updates(request: Request) -> OutputModel:
    """
    Lista las actualizaciones (comentarios) asociados a una tarea especifica en Monday.com
    """
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
        response=[ResponseMessageModel(message="Error de conexión con el cliente de Monday: {e}")]
    )

    data = await request.json()
    params = None
    try:
        params = GetItemUpdatesParams(**data)
        logger.info(params)
    except Exception as e:
        message = f"Error al recuperar los parámetros, verifique que el ID de la tarea proporcionada exista en Monday.com: {e}"
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
        message = f"Error de respuesta al solicitar la lista de actualizaciones de una tarea especifica, en Monday.com: {e}"
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
    
    message = f"No se encontraron actualizaciones asociadas a la tarea especificada."
    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

# 11 - #monday-get-docs: Lists documents in Monday.com, optionally filtered by folder 
@app.post("/monday/docs/list")
async def get_docs(request: Request) -> OutputModel:
        """        
        Lista todos los documentos disponibles en Monday.com

        Parámetros de entrada:
            limit (int): Cantidad máxima de documentos a mostrar

        Retorna:
            str: Lista de documentos legibles
        """

        invocation_id = str(uuid4())
        logger.info(invocation_id)
     
        try:
            monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
        except requests.RequestException as e:
            return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=f"Error de conexión con el cliente de Monday: {e}")]
            )            
        
        try:
            data = await request.json()
            params = GetDocsParams(**data)
            logger.info(params)
        except Exception as e:
                message = f"Error al recuperar los parámetros, verifique que existan documentos en Monday.com:: {e}"
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
                response=[ResponseMessageModel(message=f"Error de respuesta al solicitar la lista de documentos disponibles en Monday.com: {e}")]               
            )
              
        try:
            docs = (response or {}).get("data", {}).get("docs", [])
            logger.info(docs)
        except Exception as e:
            logger.info("error en el try de docs")
            return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"EError al procesar la respuesta de Monday.com: {e}")]            
        )
    
        if not docs:
            return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message="No se encontraron documentos para listar en Monday.com.")]
            )
        
        # Procesar respuesta
        lines = []
        for d in docs:
            lines.append(
                f"ID del documento: {d['id']}\n"
                f"Nombre: {d['name']}\n"
                f"Creado: {d['created_at']}\n"
                f"ID del espacio de trabajo: {d['workspace_id']}\n"
                f"ID de la carpeta: {d.get('doc_folder_id','None')}\n"
                f"Creado por: {d['created_by']['name']} (ID: {d['created_by']['id']})\n"
                "-----\n"
            )
        
        message = f"Documentos:\n\n" + "\n".join(lines)

        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

# 12 - #monday-get-doc-content: Retrieves the content of a specific document
@app.post("/monday/doc_content/get")
async def get_doc_content(request: Request) -> OutputModel:
        """
        Lista el contenido de los bloques que posee un documento de Monday.com

        Parámetros de entrada:
            doc_id (str): ID del documento

        Retorna:
            str: Lista con el contenido del documento.
        """
        invocation_id = str(uuid4())
        logger.info(invocation_id)

        try:
            monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
        except requests.RequestException as e:
            return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error de conexión con el cliente de Monday: {e}")]
        )
                
        params = None

        try:
            data = await request.json()
            params = GetDocContentParams(**data)
            logger.info(params)
        except Exception as e:
            message = f"Error al recuperar los parámetros, verifique que el ID del documento proporcionado, exista en Monday.com: {e}"
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
                response=[ResponseMessageModel(message=f"Error de respuesta al solicitar el contenido del documento en Monday.com: {e}")]               
            )

        try:
            docs = (response or {}).get("data", {}).get("docs", [])
            logger.info(docs)
        except Exception as e:
            logger.info("error en el try de docs")
            return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error al procesar la respuesta de Monday.com: {e}")]            
        )
    
        if not docs:

            message = f"No se pudo localizar el documento cuyo ID es: {params.doc_id} "
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
            response=[ResponseMessageModel(message=f"Error al procesar la respuesta de Monday.com: {e}")]            
        )       
           
        if not blocks:
            message = f"El documento: {doc['name']} cuyo ID es: (ID: {doc['id']}) no contiene bloques."            
            return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
            )

         # Procesar respuesta 
        lines = [f"Document {doc['name']} (ID: {doc['id']}):\n\nBlocks:"]
        for b in blocks:
            lines.append(f"- Block ID: {b['id']} | Type: {b['type']} | Content: {b['content']}")

        message = f"Documentos:\n\n" + "\n".join(lines)

        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

# 13 - monday-list-users: Lists all available Monday.com users
@app.get("/monday/users/list")
async def listUsers(request: Request) -> OutputModel:
    """
    Lista los usuarios de Monday.com

    Parámetros de entrada:
        
    Retorna:
        Lista de usuarios
        
    """
    invocation_id = str(uuid4())
       
    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Error de conexión con el cliente de Monday: {e}")]
    )    
      
    response = monday_client.users.fetch_users()
    users = response["data"]["users"]
    users_list = "\n".join(
        [f"- {user['name']} (ID: {user['id']})" for user in users]
    )

    message = "Usuarios disponibles en Monday.com: \n %s" % (users_list) 

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
    )


#______________________________________________________________________________________________________________
#______________________________________________________________________________________________________________
#___________________________ GET_______________________________________________________________________________

# 14 - monday-get-item-by-id: Retrieves items by theirs IDs
@app.post("/monday/item/get_item_by_id")
async def get_item_by_id(request: Request) -> OutputModel:
    """
    Lista todas las tareas a traves de los IDs especificados, en Monday.com
    """
    
    #genera id unico
    invocation_id = str(uuid4())
    monday_client = None
    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,
        status="error",
        response=[ResponseMessageModel(message="Error de conexión con el cliente de Monday: {e}")]
    )

    data = await request.json()
    params = None
    try:
        params = GetItemByIdParams(**data)
        logger.debug(params)
    except Exception as e:
        message = f"Error al recuperar el parámetro, verifique que el ID de la tarea, que ha sido proporcionado, exista en Monday.com:: {e}"
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
        message = f"Error de respuesta al solicitar el detalle de la tarea proporcionada en Monday.com: {e}"
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
        message = f"ID de la tarea: {dict_read_property_into_array(items,'id')} Descripción de la tarea: {dict_read_property_into_array(items,'name')}"
        for item_arr in arr_cols:
            logger.info(item_arr)
            message = f"{message} Columna: "
            for prop_id in dict_list_prop_id(item_arr):
                logger.info(prop_id)
                message = f"{message} {prop_id}: {dict_read_property(item_arr,prop_id)}"

        message = f"{message} tarea en Monday.com"
    else:
        logger.debug("sin respuesta")

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

# 15 - #monday-get-board-columns: Get the Columns of a Monday.com Board
@app.post("/monday/columns/get")
async def get_board_columns(request: Request) -> OutputModel:    
    """
    Lista todas las columnas de un tablero de Monday.com 
        
        Parámetros de entrada:

           boardId: ID del tablero a consultar 
        
        Retorna:
              Detalle de las columnas de cada tarea o subtarea del tablero de Monday.com 
    """
    invocation_id = str(uuid4())

    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Error de conexión con el cliente de Monday: {e}")]
    )

    data = await request.json()
    params = None 
    message = "" 

    try:
        params = GetBoardColumnsParams(**data)
    except Exception as e:
        message = f"Error al recuperar el parámetro, verifique que el ID del tablero proporcionado exista en Monday.com:: {e}"
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
       
        message = f"Columnas disponibles en el tablero de Monday.com: \n %s" % (response['data']) 

    else:
        logger.info("sin respuesta")

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        ) 

#______________________________________________________________________________________________________________
#___________________________ UPDATE____________________________________________________________________________
#______________________________________________________________________________________________________________

# 16 - monday-update-item: Update a Monday.com item's or sub-item's column values. 
@app.put("/monday/item/update")
async def update_item(request: Request) -> OutputModel:
    '''
    Update a Monday.com item's or sub-item's column values.
    Actualiza el valor de las columnas correspondientes a una tarea o subtarea de Monday.com

    Parámetros de entrada:
        boardId: ID del tablero de Monday.com al que pertenece la tarea o subtarea cuyas columnas se desean actualizar.
        itemId: ID de la tarea o subtarea de Monday.com a la cual se le actualizarán los valores de las columnas.
        columnValues: Diccionario de valores de columna para actualizar la tarea o subtarea de Monday.com con. ({column_id: valor}).        
    '''
 
    invocation_id = str(uuid4())

    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Error de conexión con el cliente de Monday: {e}")]
    )

    data = await request.json()
    params = None  

    try:
        params = UpdateItemParams(**data)
    except Exception as e:
        message = f"Error al recuperar los parámetros, verificar que el o los IDs proporcionados existan en Monday.com: {e}"
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
        message = f"Error de respuesta al solicitar la actualización de la tarea o subtarea en Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    message = ""
    if not response is None:
        #Genero el mensaje de salida
        logger.info("Procesa respuesta")        
        message = f"Tarea de Monday.com actualizada. {response['data']['change_multiple_column_values']['id']}"
        # message = f"Updated Monday.com item. {params.item_id} en el tablero cuyo ID es: : {params.board_id}."  
        # Faltan los valores de las columnas 
    else:
        logger.info("sin respuesta")

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

# 17 - monday-move-item-to-group: Moves a Monday.com item to a different group
@app.post("/monday/item/move_item_to_group")
async def move_item_to_group(request: Request) -> OutputModel:
    """
    Mover una tarea a otro grupo

       Parámetros de entrada:        
        item_Id: ID de la tarea o subtarea de Monday.com que será trasladada a otro grupo.
        group_id: ID del grupo de Monday.com donde se alojará la tarea o subtarea trasladada.

    """
    #monday-move-item-to-group
    invocation_id = str(uuid4())
    monday_client = None
    try:
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,
        status="error",
        response=[ResponseMessageModel(message="Error de conexión con el cliente de Monday: {e}")]
    )

    data = await request.json()
    params = None
    try:
        params = MoveItemToGroup(**data)
    except Exception as e:
        message = f"Error de respuesta al solicitar el traslado de una tarea a otro grupo en Monday.com:{e}"
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
        message = f"Error al trasladar la tarea a otro grupo en Monday.com:{e}"
        return OutputModel(
                invocationId=invocation_id,
                status="error",
                response=[ResponseMessageModel(message=message)]
        )
    message = ""
    if not response is None:
        #Genero el mensaje de salida
        logger.info("Procesa respuesta")
        message = f"Tarea trasladada {response['data']['move_item_to_group']['id']} a otro grupo de Monday.com"
    else:
        logger.info("sin respuesta")

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

# 18 - monday-archive-item: Archives a Monday.com item
@app.post("/monday/archive/item")
async def archive_item_by_id(request: Request) -> OutputModel:
    """
    Archivar una tarea en Monday.com

       Parámetros de entrada:
           itemId: ID de la tarea o subtarea de Monday.com que será archivada.
      
    """
    invocation_id = str(uuid4())
    monday_client = None
    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,
        status="error",        
        response=[ResponseMessageModel(message="Error de conexión con el cliente de Monday: {e}")]
    )

    data = await request.json()
    params = None
    try:
        params = ArchiveItemParams(**data)
    except Exception as e:
            message = f"Error al recuperar el parámetro, verifique que el ID de la tarea proporcionada exista en Monday.com: {e}"
            return OutputModel(
                    invocationId=invocation_id,
                    status="error",
                    response=[ResponseMessageModel(message=message)]
            )
    response = None
    try:
        response = monday_client.items.archive_item_by_id(
            item_id= params.item_id
        )
        logger.info(response)
    except Exception as e:
            message = f"Error de respuesta al solicitar que la tarea proporcionada en Monday.com sea archivada: {e}"
            return OutputModel(
                    invocationId=invocation_id,
                    status="error",
                    response=[ResponseMessageModel(message=message)]
            )
    if not response is None:
        logger.info("Procesa respuesta")
        message = f"Tarea archivada {response['data']['archive_item']['id']} en Monday.com"
    else:
        logger.info("sin respuesta")
    
    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

# 19 - monday-add-doc-block: Adds a block to an existing document
@app.post("/monday/add/block")
async def monday_add_doc_block(request: Request) -> OutputModel:
    """
    Incorporar un nuevo bloque a un documento.
    
    Parámetros de entrada:
        doc_id (str): ID del documento donde se incorporará el nuevo bloque
        block_type (str): Tipo de bloque que se incorporará (normal_text, bullet_list, etc.)
        content (str): Texto del contenido
        after_block_id (Opcional[str]): ID del bloque después del cual se realizará la inserción del nuevo bloque.

    Retorna:
        str: Confirmación con la información del nuevo bloque creado.
    """
    invocation_id = str(uuid4())
    monday_client = None
    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,
        status="error",        
        response=[ResponseMessageModel(message="Error de conexión con el cliente de Monday: {e}")]
    )

    data = await request.json()
    params = None
    try:
        params = AddDocBlockParams(**data)
    
    except Exception as e:
        message = f"Error al recuperar los parámetros, verifique que el ID ded documento proporcionado exista en Monday.com: {e}"
        return OutputModel(
            invocationId=invocation_id,
            status="error",
            response=[ResponseMessageModel(message=message)]
        )
    response = None
    
    escaped_content = params.content.replace('"', '\\"')
    after_param = f"after_block_id: {params.after_block_id}," if params.after_block_id else ""
    
    mutation = f"""
        mutation {{
            create_doc_block (
                type: {params.block_type},
                doc_id: {params.doc_id},{after_param}
                content: "{escaped_content}"
            ) {{
                id
            }}
        }}
    """

    logger.info("el mutation es: ")
    logger.info(mutation)
    try:
        response = monday_client.custom._query(mutation)
        logger.info(response)
    except requests.RequestException as e:
       logger.info(e)
       return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error de respuesta al solicitar la creación de un nuevo bloque al documento de Monday.com: {e}")]               
        )
    try:
        block = (response or {}).get("data", {}).get("create_doc_block")
        logger.info(block)
    except Exception as e:
        logger.info("error en el try de block")
        return OutputModel(
        invocationId=invocation_id,
        response=[ResponseMessageModel(message=f"Error al procesar la respuesta de Monday.com: {e}")]            
    )
    if not block is None:
        logger.info("Procesa respuesta")
        message = f"ID del bloque incorporado en Monday.com: {block['id']}"
    else:
        logger.info("sin respuesta")
    
    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

#______________________________________________________________________________________________________________
#___________________________ DELETE____________________________________________________________________________
#______________________________________________________________________________________________________________

# 20 - monday-delete-group: Deletes a Monday.com group
@app.delete("/monday/group/delete")
async def delete_group_by_id(request: Request) -> OutputModel:
    """
    Eliminar un grupo de un tablero de Monday.com 

       Parámetros de entrada: 
            board_id: ID del tablero donde se encuentra el grupo a eliminar.       
            group_id: ID del grupo que será eliminado de Monday.com .

    """
    invocation_id = str(uuid4())
    monday_client = None
    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,
        status="error",        
        response=[ResponseMessageModel(message="Error de conexión con el cliente de Monday: {e}")]
    )

    data = await request.json()
    params = None
    try:
        params = DeleteGroupByIdParams(**data)
    except Exception as e:
            message = f"Error al recuperar los parámetros, verifique que el ID del tablero y el ID del grupo proporcionados, existan en Monday.com: {e}"
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
            message = f"Error de respuesta al solicitar la eliminación del grupo especificado, en Monday.com: {e}"
            return OutputModel(
                    invocationId=invocation_id,
                    status="error",
                    response=[ResponseMessageModel(message=message)]
            )
    
    if not response is None:
        logger.info("Procesa respuesta")
        message = f"ID del Grupo eliminado en Monday.com:  {response['data']['delete_group']['id']}"
    else:
        logger.info("sin respuesta")
    
    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )

# 21 - monday-delete-item: Deletes a Monday.com item
@app.delete("/monday/item/delete")
async def delete_item_by_id(request: Request) -> OutputModel:
    """
    Eliminar una tarea de Monday.com

       Parámetros de entrada:
            item_id: ID de la tarea o subtarea de Monday.com que será eliminada.

    """
    invocation_id = str(uuid4())
    monday_client = None
    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,
        status="error",        
        response=[ResponseMessageModel(message="Error de conexión con el cliente de Monday: {e}")]
    )

    data = await request.json()
    params = None
    try:
        params = DeleteItemByIdParams(**data)
    except Exception as e:
            message = f"Error al recuperar el parámetro, verifique que el ID de la tarea proporcionados, exista en Monday.com: {e}"
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
            message = f"Error de respuesta al solicitar la eliminación de la tarea especificada, en Monday.com: {e}"
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


#______________________________________________________________________________________________________________
#___________________________ OTHERS____________________________________________________________________________
#______________________________________________________________________________________________________________


@app.post("/monday/board/fetch_items_by_board_id")
async def fetch_items_by_board_id(request: Request) -> OutputModel:
    """
    Lista las tareas contenidas en un tablero de Monday.com

    Parámetros de entrada:
        board_id (str): ID del tablero.

    Retorna:
        Una lista de grupos, tareas y subtareas contenidas en el tablero especificado.
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
        response=[ResponseMessageModel(message="Error al recuperar el parámetro, verifique que el ID del tablero proporcionado, exista en Monday.com: {e}")]
    )

    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Error de conexión con el cliente de Monday: {e}")]
    )
    
    try:
        board = monday_client.boards.fetch_items_by_board_id(
            board_ids= params.board_id
        )
        logger.debug(board)
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message=f"Error de respuesta al solicitar el listado de las tareas que posee un tablero especificado en Monday.com: {e}")]
    )
    
    obj_boards = Board()
    
    #Recolecto informacion de la respuesta para enviar al template de jinja
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

    #Aplico template de jinja
    template = template_env.get_template("response_template_fetch_items_by_board_id.jinja")
    message = template.render(
        obj_boards= obj_boards
    )
    logger.info(message)


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

@app.post("/monday/columns/create")
async def create_column(request: Request) -> OutputModel:
    """
    Crea una nueva columna en Monday. com 
    
    Parámetros de entrada: 
        board_id: ID del tablero
        column_title: Nombre de la columna que se incorporará 
        column_type: Tipo de columna          
        defaults: Valores predeterminados de la nueva columna (json).     

    """
    #Creo un identificador unico
    invocation_id = str(uuid4())
    try: 
        #Abro conexion
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id, 
        response=[ResponseMessageModel(message="Error de conexión con el cliente de Monday: {e}")]
    )
    #Traigo los datos del request
    data = await request.json()
    params = None
    
    try:
        #parseo los datos del request
        logger.info("Parse input")
        params = CreateColumnParams(**data)
        logger.info(params)
    except Exception as e:
        message = f"Error al recuperar los parámetros, verifique que el ID del tablero proporcionado, exista en Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    
    # Manejo de defaults → string JSON escapado
    defaults_str = ""
    if params.defaults is not None:
        defaults_json = json.dumps(params.defaults, ensure_ascii=False)
        defaults_str = f', defaults: "{defaults_json.replace("\"", "\\\"")}"'

    # Construir mutación GraphQL
    mutation = f"""
        mutation {{
            create_column (
                board_id: {params.board_id},
                title: "{params.column_title}",
                column_type: {params.column_type or "text"}
                {defaults_str}
            ) {{
                id
            }}
        }}
    """

    logger.info("Mutación enviada a Monday:")
    logger.info(mutation)

    # Ejecutar mutación
    try:
        response = monday_client.custom._query(mutation)
        logger.info(response)
    except requests.RequestException as e:
        return OutputModel(
            invocationId=invocation_id,
            status="error",
            response=[ResponseMessageModel(message=f"Error de respuesta al solicitar la creación de columna en Monday.com: {e}")]
        )

    # Procesar respuesta
    try:
        column = (response or {}).get("data", {}).get("create_column")
    except Exception as e:
        return OutputModel(
            invocationId=invocation_id,
            status="error",
            response=[ResponseMessageModel(message=f"Error al procesar la respuesta de Monday.com: {e}")]
        )

    # Generar mensaje de salida
    if column:
        message = f"Columna creada en Monday.com con ID: {column['id']}"
    else:
        message = "No se recibió respuesta de Monday.com al crear la columna."

    return OutputModel(
        invocationId=invocation_id,
        status="success",
        response=[ResponseMessageModel(message=message)]
    )

    
    '''
    
    response = None

    #llamada al servicio de monday
       #Imprimo la respuesta
    try:
        logger.info("Ejecuta api monday")

        response = monday_client.columns.create_column(
            board_id= params.board_id,
            column_title= params.column_title,
            column_type= params.column_type,
            #,#No logro identificar el valor del tipo de columna para que pueda crearla
            #column_type= 0,
            defaults= params.defaults
        )
    
        logger.debug(response)
    except Exception as e:
        message = f"Error de respuesta al solicitar la creación de una nueva columna en el tablero de Monday.com especificado: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    
    message = ""
    if not response is None:
        #Genero el mensaje de salida
        logger.info("Procesa respuesta")
        message = f"Sucessfull create column {response['data']['create_column']['id']} Monday.com"
    else:
        logger.info("sin respuesta")

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )
'''

def process_excel(params:OpenExcel,monday_client:MondayClient,invocation_id:str):
    """
        Proceso que se dispara en un hilo separado desde open_excel
    """
    excel_monday = ExcelUtilsMonday()
    excel_monday.esperar = params.esperar
    excel_monday.wait_time = 3
    uid = invocation_id
    if params.continuar:
        uid = params.uid
    excel_monday.process_excel_monday(params.file_name,params.download,monday_client,uid,params.rows,params.continuar)


@app.post("/monday/analizar_excel")
async def analizar_excel(request: Request) -> OutputModel:
    invocation_id = str(uuid4())
    
    data = await request.json()
    params = None
    try:
        #parseo los datos del request
        logger.info("Parse input")
        params = OpenExcel(**data)
    except Exception as e:
        message = f"Parse error on imput request message Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                status="error",
                response=[ResponseMessageModel(message=message)]
        )
    excel_monday = ExcelUtilsMonday()
    uid = invocation_id
    if params.continuar:
        uid = params.uid
    arr_analisis = excel_monday.analizar_excel(params.file_name,params.download,uid)

    message = ""
    template = template_env.get_template("response_template_analiza_excel.jinja")
    message = template.render(
        arr_analisis = arr_analisis
    )
    logger.info(message)
    return OutputModel(
            invocationId=invocation_id,
            status="error",
            response=[ResponseMessageModel(message=message)]
    )


#monday-open_excel: -----------COMPLETAR-----------------
@app.post("/monday/read_excel")
async def open_excel(request: Request) -> OutputModel:
    """Abre un archivo excel y procesa los datos creando boards grupos e items
        file_name = ruta del archivo a ser procesado o url para descarga del archivo
        download = si donlowad esta en true el parametro file_name se interpretara como una url y se descargara el archivo para procesarlo
        rows = si el parametro rows es = 0 se procesaran todas las filas del documento si es otro numero se procesaran la cantidad de filas especificadas
        uid = si se desea continuar un proceso que finalizo con error o un proceso parcial se debe proporcionar el identificador de la transaccion previa
        continuar = si se desea continuar un proceso finalizado con error o un proceso parcial este parametro debe estar en True
        esperar = este parametro espera un tiempo antes de mandar el siguiente request a monday para evitar errores de conexion debe estar en true para aplicar los tiempos de espera
    """
    
    invocation_id = str(uuid4())
    
    data = await request.json()
    params = None
    try:
        #parseo los datos del request
        logger.info("Parse input")
        params = OpenExcel(**data)
    except Exception as e:
        message = f"Parse error on imput request message Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                status="error",
                response=[ResponseMessageModel(message=message)]
        )
    try:
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
        
        thread = Thread(target=process_excel,args=(params,monday_client,invocation_id))
        thread.start()

    except requests.RequestException as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error de conexión con el cliente de Monday: {e}")]
        )
    #Mensaje de retorno
    template = template_env.get_template("response_template_process_excel.jinja")
    message = template.render(
        file_name = params.file_name
    )

    return OutputModel(
        invocationId=invocation_id,
        response=[ResponseMessageModel(message=message)]
    )



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000, log_level="info")