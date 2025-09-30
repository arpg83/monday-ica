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

from schemas import ResponseMessageModel, OutputModel, CreateBoardParams, CreateBoardGroupParams, CreateItemParams, ListBoardsParams, GetBoardGroupsParams, UpdateItemParams, CreateUpdateCommentParams,FetchItemsByBoardId, DeleteItemByIdParams,MoveItemToGroup,GetItemUpdatesParams,GetItemByIdParams, ListItemsInGroupsParams, OpenExcel, ListSubitemsParams, GetBoardColumnsParams, CreateDocParams, DeleteGroupByIdParams, ArchiveItemParams, GetDocsParams, GetDocContentParams, AddDocBlockParams, CreateColumnParams,CreateSubitemParams,ProcessExcelStatus, DeleteColumnByIdParams

from monday import MondayClient
from monday.resources.types import BoardKind
from fastapi.responses import JSONResponse
from open_excel_utils import *

from response_classes import *

import json
from threading import Thread
# Clase para usar en el template para listar usuarios
from usuarios_response import Usuario 

load_dotenv()
hilos = []

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
        board_kind (str): La clase de tablero a crear. Debe ser "publico" o "privado".

    Retorna:
        board_id: ID del tablero creado
    """
    invocation_id = str(uuid4())
    data = await request.json()

    params = None
    message = ""        
   
    try: 
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
        invocationId=invocation_id,        
        response=[ResponseMessageModel(message="Error de conexión con el cliente de Monday: {e}")]
    )

    try:
        params = CreateBoardParams(**data)
    except Exception as e:
        message = f"Error al recuperar los parámetros, nombre y tipo de tablero para crearlo en Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
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

    params = None

    try:
        params = CreateItemParams(**data)
        logger.info(params)
    except Exception as e:
        message = f"Error al recuperar los parámetros, verificar que el o los IDs proporcionados existan en Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    
    message = ""
    response = None

    try:
        response = monday_client.items.create_item(
                board_id=params.board_id,
                group_id=params.group_id,
                item_name=params.item_name,
                column_values=params.column_values,
                create_labels_if_missing=params.create_labels_if_missing
        )
        logger.info(response)
    except Exception as e:
            message = f"Error de respuesta al solicitar la creación de la tarea en Monday.com:{e}"
            return OutputModel(
                    invocationId=invocation_id,
                    response=[ResponseMessageModel(message=message)]
            )
    
    message = ""
    if not response is None:
        #Genero el mensaje de salida
        logger.info("Procesa respuesta")  
        
    #    message = f"Created new item: in group: {params.group_name} in board: {params.board_id}. ID of the item: {response['data']['create_item']['id']}"
    
        template = template_env.get_template("response_template_item_created_v2.jinja")
        message = template.render(
           item_name = params.item_name,
            board_id = params.board_id,
            group_id = params.group_id,
            item_id = response['data']['create_item']['id'],                
            column_values = params.column_values,
            create_labels_if_missing=params.create_labels_if_missing
        )
    
    else:
        logger.info("sin respuesta")
        message = f"No se pudo crear la tarea en Monday.com."
    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        ) 
 
# 22 - monday-create-subitem: Creates a new sub-item in a Monday.com item
@app.post("/monday/subitem/create")
async def create_subitem(request: Request) -> OutputModel:
    """
    Crea una subtarea nueva en una tarea de Monday.com. 
    
    Parámetros de entrada:
        subitem_name: Nombre de la subtarea
        parent_item_id: Id de la tarea donde se creará la subtarea.
        column_values: Nombres de las columnas asociadas a la subtarea que se creará.(Opcional)


    Devuelve:
        Detalle incluyendo el ID de la subtarea creada.
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

    params = None

    try:
        params = CreateSubitemParams(**data)
        logger.info(params)
    except Exception as e:
        message = f"Error al recuperar los parámetros, verificar que el o los IDs proporcionados existan en Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    
    message = ""
    response = None

    try:
        response = monday_client.items.create_subitem (
                parent_item_id=params.parent_item_id,
                subitem_name=params.subitem_name,
                column_values=params.column_values,
                create_labels_if_missing=params.create_labels_if_missing)

        logger.info(response)
    except Exception as e:
            message = f"Error de respuesta al solicitar la creación de la subtarea en Monday.com:{e}"
            return OutputModel(
                    invocationId=invocation_id,
                    response=[ResponseMessageModel(message=message)]
        )
    
    message = ""
    if not response is None:
        #Genero el mensaje de salida
        logger.info("Procesa respuesta")  
        
    #    message = f"Created new subitem: in item: {params.parent_item_id}. ID of the subitem: {response['data']['create_subitem']['id']}"
    
        template = template_env.get_template("response_template_subitem_created.jinja")
        message = template.render(
           subitem_name = params.subitem_name,
           parent_item_id = params.parent_item_id,        
           subitem_id = response['data']['create_subitem']['id'],                
           column_values = params.column_values,
           create_labels_if_missing=params.create_labels_if_missing)
    
    else:
        logger.info("sin respuesta")
        message = f"No se pudo crear la subtarea en Monday.com."
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
        logger.info(params)
    except Exception as e:
        message = f"Error al recuperar los parámetros, verificar que el ID de la tarea exista en Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    
    response = None
    try:
        #llamada al servicio de monday
        response = monday_client.updates.create_update(item_id=params.item_id, update_value=params.update_value)

        #Imprimo la respuesta
        logger.info(response)
    except Exception as e:
        message = f"Error de respuesta al solicitar la creación de la actualización (comentario) de una tarea o subtares en Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message=message)]
        )
    error = False
    if response is None:
        error = True

    template = template_env.get_template("response_template_comment_update.jinja")
    message = template.render(
        update_id = response['data']['create_update']['id'],
        error = error
    )

#    message = ""
#    if response is not None:
#        #Genero el mensaje de salida
#        logger.info("Procesa respuesta")        
#        message = f"Se creó una nueva actualización (comentario) en la tarea o subtarea especificada en Monday.com: {response['data']['create_update']['id']}"
#    else:
#        logger.info("sin respuesta")
#        message = f"No se pudo crear la nueva actualización (comentario) en la tarea o subtarea especificada en Monday.com."
      
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
        message = f"Error al recuperar los parámetros, verificar que el ID del espacio de trabajo o el ID del item proporcionado, exista en Monday.com: {e}"
        return OutputModel(
            invocationId=invocation_id,
            status="error",
            response=[ResponseMessageModel(message=message)]
        )
    
    if params.workspace_id:
        if not params.kind:
            message = "'kind' es requerido cuando se utiliza el ID del espacio de trabajo."
        location = f'location: {{workspace: {{ workspace_id: "{params.workspace_id}", name: "{params.title}", kind: {params.kind} }} }}'
    elif params.item_id or params.column_id:
        if not params.item_id or not params.column_id:
            message =  "'item_id' y 'column_id' son requeridos."
        location = f'location: {{board: {{ column_id: "{params.column_id}", item_id: {params.item_id}}} }}' 
    else:
        message =  "Puede ingresar el ID del Espacio de trabajo o el ID del Item y ID de Columna."
        return OutputModel(
            invocationId=invocation_id,
            status="error",
            response=[ResponseMessageModel(message=message)]
        )   
     
    response = None
    mutation = f"""
        mutation {{
            create_doc (
                {location}
            ) {{
                id
            }}
        }}
    """
    logger.info(mutation)
    try:
        response = monday_client.custom._query(mutation)
        logger.info(response)
    except Exception as e:
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

    # metodo para asignarle el nombre al archivo - pero no esta respondiendo la api
    '''
    mutation = f"""
        mutation {{
            update_doc_name (
                docId: {doc_id}, 
                name: "{params.title}"
            )
        }}
    """
    logger.info(mutation)
    try:
        response = monday_client.custom._query(mutation)
        logger.info(response)
    except Exception as e:
        logger.info("sin respuesta")
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error de respuesta al solicitar la actualizacion de nombre del documento en Monday.com: {e}")]               
        )
    try:
        updated = (response or {}).get("data", {}).get("update_doc_name")
        logger.info(updated)
    except Exception as e:
        logger.info("error en el try de updated")
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error al procesar la respuesta de Monday.com: {e}")]            
        )
    '''
    try:
            monday_url = os.getenv("MONDAY_WORKSPACE_URL")
            doc_url = f"{monday_url}/docs/{doc_id}"
    except NameError:
            doc_url = f"(La URL del Espacio de trabajo no está configurada) Doc ID {doc_id}"

    #Hacer Template response_template_doc_create.jinja  tomado por LR

    message = f"El documento fue creado exitosamente!\nTitulo: {params.title}\nID del documento: {doc_id}\nURL: {doc_url}"

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
        )
   
# 23 -  monday-create-column: Crea a Monday.com column
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
        defaults_json_escaped = defaults_json.replace("\"", "\\\"")
        defaults_str = f', defaults: "{defaults_json_escaped}"'

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

    #Hacer Template response_template_column_create.jinja

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
    
    #Hacer Template response_template_boards_list.jinja
    
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
    
    #Hacer Template response_template_boards_group_get.jinja

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
    '''
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
    '''

    if response is not None:
        try:
            boards = response.get("data", {}).get("boards", [])
            if not boards:
                raise ValueError("No se encontraron tableros en la respuesta.")
            groups = boards[0].get("groups", [])
            if not groups:
                return OutputModel(
                    invocationId=invocation_id,
                    response=[ResponseMessageModel(message="No se encontraron grupos en el tablero especificado.")]
                )
        except (KeyError, IndexError, TypeError, ValueError) as e:
            logger.error(f"Estructura inesperada en la respuesta de Monday.com: {e}")
            return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message="Error: la respuesta no contiene grupos válidos.")]
            )

        # DEBUG: imprimir estructura        
        logger.info("Contenido de 'groups':\\n" + json.dumps(groups, indent=2, ensure_ascii=False))

        # Renderizar template
        template = template_env.get_template("response_template_list_items_in_groups.jinja")
        message = template.render(
            board_id=params.board_id,
            groups=groups
        )

    else:
        logger.info("Sin respuesta")
        message = "No se encontraron tareas en los grupos especificados."

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

    #Hacer Template response_template_item_list.jinja

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
    
    #Hacer Template response_template_get_item_updates.jinja  (Es bastante complejo)

    message = ""
    if response is not None:
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
            object_ids List[int]: Lista de los IDs de los documentos a visualizar
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
            docs (object_ids: {params.object_ids}, limit: {params.limit}) {{
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
            response=[ResponseMessageModel(message=f"Error al procesar la respuesta de Monday.com: {e}")]            
        )
    
        if not docs:
            return OutputModel(
                invocationId=invocation_id,
                response=[ResponseMessageModel(message="No se encontraron documentos para listar en Monday.com.")]
            )
        
        #Hacer Template response_template_docs_list.jinja (Es complejo para la parametria)

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
         #Hacer Template response_template_doc_content_get.jinja

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
#async def listUsers(request: Request) -> OutputModel:
async def listUsers() -> OutputModel:
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
      
   # response = monday_client.users.fetch_users()
   # users = response["data"]["users"]
   # users_list = "\n".join(
   #     [f"- {user['name']} (ID: {user['id']})" for user in users]
   # )

   # message = "Usuarios disponibles en Monday.com: \n %s" % (users_list) 
    response = monday_client.users.fetch_users()
    users = response["data"]["users"]
    usuarios = []
    for user in users:
        usuario = Usuario()
        usuario.id = user["id"]
        usuario.name = user["name"]
        usuario.email = user["email"]
        usuario.enabled = user["enabled"]
        usuario.teams = user["teams"]
        usuarios.append(usuario)

    # Configurar el entorno de plantillas de Jinja2
    file_loader = FileSystemLoader(searchpath="./")
    env = Environment(loader=file_loader)

    # Renderizar la plantilla con los datos
    template = env.get_template('templates/response_template_users.jinja')

    message = template.render(users=usuarios,cant_users=int(len(usuarios)))

    # Imprimir el mensaje resultante
    logger.info(message)

    return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=message)]
    )

# 25 - monday-list-workspaces: Lists all available Monday.com workspaces
@app.post("/monday/workspaces/list")
async def listWorkspaces(request: Request) -> OutputModel:
    """
    Lista todos los espacios de trabajo de Monday.com directamente (sin pasar por boards)
    """
    invocation_id = str(uuid4())

    # Conectar con el cliente Monday
    try:
        monday_client = MondayClient(os.getenv("MONDAY_API_KEY"))
    except requests.RequestException as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error de conexión con el cliente de Monday: {e}")]
        )

    # Query GraphQL directa para listar workspaces
    query = """
    query {
        workspaces {
            id
            name
            kind
            description
        }
    }
    """

    try:
        response = monday_client.custom._query(query)
        logger.info(response)
    except requests.RequestException as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error al solicitar la lista de workspaces de Monday.com: {e}")]
        )

    # Procesar respuesta
    try:
        workspaces_data = response.get("data", {}).get("workspaces", [])
    except Exception as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error al procesar la respuesta de Monday.com: {e}")]
        )

    # Construir el mensaje de salida
    #Hacer Template response_workspaces_list.jinja
    if workspaces_data:
        lines = []
        for w in workspaces_data:
            lines.append(
                f"ID del espacio de trabajo: {w.get('id')}\\n"
                f"Nombre: {w.get('name')}\\n"
                f"Descripción: {w.get('description')}\\n"
                f"Tipo de espacio de trabajo: {w.get('kind')}\\n"
                "-----\\n"
            )
        message = f"Workspaces:\n\n" + "\n".join(lines)
        #message = "Workspaces:\\n\ " + "\\n".join(lines)
    else:
        message = "No se encontraron workspaces en Monday.com."

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
            ids = json.dumps(params.items_id)
        )
        #Imprimo la respuesta
        logger.info(response)
    except Exception as e:
        message = f"Error de respuesta al solicitar el detalle de la tarea proporcionada en Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                status="error",
                response=[ResponseMessageModel(message=message)]
        )
    message = ""
    if not response is None:

        '''
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

        '''
        # Extraer lista de items
        items = response["data"]["items"]

        # Normalizar para evitar errores en Jinja
        for item in items:
            if "board" not in item:
                item["board"] = {"id": None, "name": None}
            if "group" not in item:
                item["group"] = {"id": None, "title": None}
        
        # Renderizar template Jinja (texto plano)
        template = template_env.get_template("response_template_list_items_by_ids.jinja")  
        message = template.render(items=items)       

    else:
        logger.debug("sin respuesta")
        message = f"No se recuperaron tareas para los IDs indicados en Monday.com."

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

    '''
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
    
    '''          
    #Hacer Template response_template_columns_get.jinja
    if not response is None:

       
        #Genera el mensaje de salida
        logger.info("Procesa respuesta")        
        
        # message = f"Columnas disponibles en el tablero de Monday.com: \n %s" % (response['data']) 

        columns = response["data"]["boards"][0]["columns"]

        template = template_env.get_template("response_template_get_board_columns.jinja")
        message = template.render(columns=columns)

    else:
        logger.info("sin respuesta")
        message = f"No se recuperaron columnas para el tablero indicado en Monday.com."

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
            column_values=params.column_values,
            create_labels_if_missing=params.create_labels_if_missing
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
    #Hacer Template response_template_item_update.jinja
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
    
    #Hacer Template response_move_item_to_group.jinja
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
    #Hacer Template response_template_archive_item.jinja
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
    
    content_doc = f'{{\"deltaFormat\":[{{\"insert\":\"{params.content}\"}}]}}'
    escaped_content = content_doc.replace('"', '\\"')

    if params.after_block_id:
        mutation = f"""
        mutation {{
            create_doc_block (
                type: {params.block_type},
                doc_id: {params.doc_id},
                after_block_id: "{params.after_block_id}",
                content: "{escaped_content}"
            ) {{
                id
            }}
        }}
        """
    else:
        mutation = f"""
        mutation {{
            create_doc_block (
                type: {params.block_type},
                doc_id: {params.doc_id},
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

    #Hacer Template response_template_doc_add_block.jinja
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
@app.post("/monday/group/delete")
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
    #Hacer Template response_template_group_delete.jinja
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
@app.post("/monday/item/delete")
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

# 24 -  monday-delete-column: Deletes a Monday.com column
@app.post("/monday/column/delete")
async def delete_column_by_id(request: Request) -> OutputModel:
    """
    Eliminar una columna de un tablero de Monday.com 

       Parámetros de entrada: 
            board_id: ID del tablero donde se encuentra el grupo a eliminar.                 
            column_id: ID de la columna que será eliminada de Monday.com .

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
        params = DeleteColumnByIdParams(**data)
    except Exception as e:
            message = f"Error al recuperar los parámetros, verifique que el ID del tablero y el ID de la columna proporcionados, existan en Monday.com: {e}"
            return OutputModel(
                    invocationId=invocation_id,
                    status="error",
                    response=[ResponseMessageModel(message=message)]
            )
    response = None
 
    mutation = f"""
        mutation {{
            delete_column (
                board_id: "{params.board_id}",
                column_id: "{params.column_id}"                
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
            response=[ResponseMessageModel(message=f"Error de respuesta al solicitar la eliminación de la columna de Monday.com: {e}")]               
        )
    
    sin_respuesta = False
    id = None
    #Hacer Template response_template_column_delete.jinja
    if response is None:
        sin_respuesta = True
    else: 
        id = response['data']['delete_column']['id']

    template = template_env.get_template("response_template_column_delete.jinja")
    message = template.render(
        column_id = id,
        sin_respuesta = sin_respuesta
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
        logger.info(board)
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

def process_excel(hilo:Hilo,params:OpenExcel,monday_client:MondayClient,invocation_id:str):
    """
        Proceso que se dispara en un hilo separado desde open_excel
    """
    excel_monday = ExcelUtilsMonday()
    hilo.proceso_excel = excel_monday
    excel_monday.esperar = (params.esperar == "True")
    excel_monday.wait_time = 3
    uid = invocation_id
    continuar = (params.continuar == "True")
    descargar = (params.download == "True")
    if continuar:
        logger.info("Entro")
        uid = params.uid
        logger.info(uid)
    excel_monday.process_excel_monday(params.file_name,descargar,monday_client,uid,params.rows,continuar)

@app.post("/monday/estado_proceso_excel")
async def estado_proceso(request: Request) -> OutputModel:
    """Devuelve el estado del procesamiento del excel"""
    invocation_id = str(uuid4())   
    data = await request.json()
    params = None
    try:
        #parseo los datos del request
        logger.info("Parse input")
        params = ProcessExcelStatus(**data)
    except Exception as e:
        message = f"Parse error on imput request message Monday.com: {e}"
        return OutputModel(
                invocationId=invocation_id,
                status="error",
                response=[ResponseMessageModel(message=message)]
        )
    purgar_inactivos = (str(params.purgar_inactivos).lower() == "true")
    purgar_procesos_antiguos = (str(params.purgar_procesos_antiguos).lower() == "true")
    detener = (str(params.detener).lower() == "true")
    uid = params.uid
    
    msg_error = ""
    arr_msg = []
    arr_proceso_antiguos = []

    if purgar_inactivos:
        arr = []
        for hilo in hilos:
            if not hilo.proceso_excel.procesando:
                arr.append(hilo)
        for hilo in arr:
            hilos.remove(hilo)
        msg_error = "Se purgaron los procesos inactivos"
        arr_msg.append(msg_error)

    util =  ExcelUtilsWorks()
    
    for item in util.listar():
        logger.info(item)
        encontro = False
        for hilo in hilos:
            if item == hilo.proceso_excel.uid:
                encontro = True
        if not encontro:
            arr_proceso_antiguos.append(item)
        if purgar_procesos_antiguos:
            if not encontro:
                logger.info(f"purga {item}" )
                if util.purgar(item):
                    arr_msg.append(f"purgo: {item}")
        

    if detener:
        if not uid == None and uid != "":
            encontro = False
            for hilo in hilos:
                if hilo.proceso_excel.uid == uid:
                    hilo.proceso_excel.detener = True
                    msg_error = f"Deteniendo proceso {uid}"
                    arr_msg.append(msg_error)
                    encontro = True
            if not encontro:
                msg_error = f"No se encontro el proceso {uid}"
                arr_msg.append(msg_error)
        else:
            msg_error = "Debe proporcionarse un uid para poder detener un proceso"
            arr_msg.append(msg_error)

    message = ""
    informacion_uid = ""
    if uid != None and uid != "":
        excel_monday = ExcelUtilsMonday()
        excel_monday.uid = uid
        if excel_monday.read_estado():
            informacion_uid = excel_monday.listar_estado_texto()



    
    template = template_env.get_template("response_template_estado_proceso_excel.jinja")
    cant_procesos = len(hilos)
    message = template.render(
        procesos_activos = hilos,
        cant_procesos = cant_procesos,
        msg_error = arr_msg,
        arr_proceso_antiguos = arr_proceso_antiguos,
        informacion_uid = informacion_uid
    )

    logger.info(message)
    return OutputModel(
            invocationId=invocation_id,
            status="ok",
            response=[ResponseMessageModel(message=message)]
    )

@app.post("/monday/analizar_excel")
async def analizar_excel(request: Request) -> OutputModel:
    """Analiza el excel"""
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
    continuar = (params.continuar == "True")
    descargar = (params.download == "True")
    if continuar:
        uid = params.uid
    arr_analisis = excel_monday.analizar_excel(params.file_name,descargar,uid)

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

# 26 - monday-import-info-from-excel: Read excel and create board, group, item, subitem, column containing information from excel rows on Monday.com 
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
        hilo = Hilo()
        hilo.hilo = Thread(target=process_excel,args=(hilo,params,monday_client,invocation_id))
        hilo.hilo.start()
        hilos.append(hilo)

    except requests.RequestException as e:
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error de conexión con el cliente de Monday: {e}")]
        )
    #Mensaje de retorno
    template = template_env.get_template("response_template_process_excel.jinja")
    message = template.render(
        file_name = params.file_name,
        uid = invocation_id
    )

    return OutputModel(
        invocationId=invocation_id,
        response=[ResponseMessageModel(message=message)]
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000, log_level="info")