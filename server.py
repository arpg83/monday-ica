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


@app.get("/monday/boards/list")
async def ListBoards(request: Request) -> OutputModel:
    """
    List boards from Monday.

    Args:
        params: The parameters for listing boards.
           limit: Optional[int] = Field(10, description="Maximum number of records to return")
           offset: Optional[int] = Field(0, description="Offset to start from")
           priority: Optional[str] = Field(None, description="Filter by priority")
           assignment_group: Optional[str] = Field(None, description="Filter by assignment group")
           timeframe: Optional[str] = Field(None, description="Filter by timeframe (upcoming, in-progress, completed)")
           query: Optional[str] = Field(None, description="Additional query string")


    Returns:
        A list of boards.
    """
    invocation_id = str(uuid4())
    data = await request.json()
    # Unwrap and validate parameters
    result = _unwrap_and_validate_params(
        data, 
        ListBoardsParams
    )
    
    if not result["success"]:
        return OutputModel(
            status="error",
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=result.get("message", "Invalid parameters"))]
        )
    
    validated_params = result["params"]
    
    # Build the query
    query_parts = []
    
    if validated_params.priority:
        query_parts.append(f"priority={validated_params.priority}")
    if validated_params.assignment_group:
        query_parts.append(f"assignment_group={validated_params.assignment_group}")
    
    # Handle timeframe filtering
    if validated_params.timeframe:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if validated_params.timeframe == "upcoming":
            query_parts.append(f"start_date>{now}")
        elif validated_params.timeframe == "in-progress":
            query_parts.append(f"start_date<{now}^end_date>{now}")
        elif validated_params.timeframe == "completed":
            query_parts.append(f"end_date<{now}")
    
    # Add any additional query string
    if validated_params.query:
        query_parts.append(validated_params.query)
    
    # Combine query parts
    query = "^".join(query_parts) if query_parts else ""
    
    # Get the instance URL
    instance_url = os.getenv("MONDAY_INSTANCIA")
    
    # Get the headers
    headers = {"Accept": "application/json"}
    
    # Make the API request
    url = f"{instance_url}/api/now/table/incident"
    
    params = {
        "sysparm_limit": validated_params.limit,
        "sysparm_offset": validated_params.offset,
        "sysparm_query": query,
        "sysparm_display_value": "true",
    }
    
    try:
        response = requests.get(url, 
                                auth=HTTPBasicAuth(os.getenv("SERVICENOW_USUARIO"), os.getenv("SERVICENOW_CONTRASENA")), 
                                headers=headers, 
                                params=params)
        response.raise_for_status()
        
        # Handle the case where result["result"] is a list
        result_json = response.json()
        epics = result_json.get("result", [])
        count = len(epics)
        
        response_template = template_env.get_template("response_template_epics.jinja")
        rendered_response = response_template.render(count=count, epics=epics) if count > 0 else "No epics found"

        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=rendered_response)]
        )
    except requests.RequestException as e:
        logger.error(f"Error listing epics: {e}")
        return OutputModel(
            invocationId=invocation_id,
            response=[ResponseMessageModel(message=f"Error listing epics: {str(e)}")]
        )

#monday-get-board-groups: Retrieves all groups from a specified Monday.com board
#monday-get-item-updates: Retrieves updates/comments for a specific item
#monday-get-docs: Lists documents in Monday.com, optionally filtered by folder
#monday-get-doc-content: Retrieves the content of a specific document


#monday-list-boards: Lists all available Monday.com boards
#monday-list-items-in-groups: Lists all items in specified groups of a Monday.com board
#monday-list-subitems-in-items: Lists all sub-items for given Monday.com items


#monday-create-item: Creates a new item or sub-item in a Monday.com board
#monday-create-update: Creates a comment/update on a Monday.com item
#monday-create-board: Creates a new Monday.com board
#monday-create-board-group: Creates a new group in a Monday.com board
#monday-create-doc: Creates a new document in Monday.com

#monday-add-doc-block: Adds a block to an existing document
#monday-move-item-to-group: Moves a Monday.com item to a different group
#monday-archive-item: Archives a Monday.com item

#monday-delete-item: Deletes a Monday.com item


def _unwrap_and_validate_params(params: Any, model_class: Type[T], required_fields: List[str] = None) -> Dict[str, Any]:
    """
    Helper function to unwrap and validate parameters.
    
    Args:
        params: The parameters to unwrap and validate.
        model_class: The Pydantic model class to validate against.
        required_fields: List of required field names.
        
    Returns:
        A tuple of (success, result) where result is either the validated parameters or an error message.
    """
    # Handle case where params might be wrapped in another dictionary
    if isinstance(params, dict) and len(params) == 1 and "params" in params and isinstance(params["params"], dict):
        logger.warning("Detected params wrapped in a 'params' key. Unwrapping...")
        params = params["params"]
    
    # Handle case where params might be a Pydantic model object
    if not isinstance(params, dict):
        try:
            # Try to convert to dict if it's a Pydantic model
            logger.warning("Params is not a dictionary. Attempting to convert...")
            params = params.model_dump() if hasattr(params, "model_dump") else dict(params)
        except Exception as e:
            logger.error(f"Failed to convert params to dictionary: {e}")
            return {
                "success": False,
                "message": f"Invalid parameters format. Expected a dictionary, got {type(params).__name__}",
            }
    
    # Validate required parameters are present
    if required_fields:
        for field in required_fields:
            if field not in params:
                return {
                    "success": False,
                    "message": f"Missing required parameter '{field}'",
                }
    
    try:
        # Validate parameters against the model
        validated_params = model_class(**params)
        return {
            "success": True,
            "params": validated_params,
        }
    except Exception as e:
        logger.error(f"Error validating parameters: {e}")
        return {
            "success": False,
            "message": f"Error validating parameters: {str(e)}",
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000, log_level="info")