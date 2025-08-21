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
class ListUsersParams(BaseModel):
    """Parameters for listing users."""

    limit: int = Field(10, description="Maximum number of users to return")
    offset: int = Field(0, description="Offset for pagination")
    active: Optional[bool] = Field(None, description="Filter by active status")
    department: Optional[str] = Field(None, description="Filter by department")
    query: Optional[str] = Field(
        None,
        description="Case-insensitive search term that matches against name, username, or email fields. Uses Monday's LIKE operator for partial matching.",
    )


#monday-create-board: Creates a new Monday.com board
#monday-create-board-group: Creates a new group in a Monday.com board
#monday-create-item: Creates a new item or sub-item in a Monday.com board
#monday-create-update: Creates a comment/update on a Monday.com item
#monday-create-doc: Creates a new document in Monday.com


class CreateBoardParams(BaseModel):
    """Parameters for creating a board."""

    monday_client: str = Field(..., description="Monday client")
    board_name: Optional[str] = Field(None, description="Name of the board")
    board_king: Optional[str] = Field("public", description="The kind of board to create")

class CreateGroupInBoardParams(BaseModel):
    """Parameters for creating a new group in a board."""

    monday_client: str = Field(..., description="Monday client")
    board_id: Optional[str] = Field(None, description="ID of the board")
    group_name: Optional[str] = Field(None, description="Name of the group")
    
class CreateItemParams(BaseModel):
    """Parameters for creating a new item or a subitem."""
    """Create a new item in a Board. Optionally, specify the parent Item ID to create a Sub-item."""

    board_id: str = Field(..., description="ID of the board")
    item_name: str = Field(..., description="Name of the item or subitem")
    monday_client: str = Field(..., description="Monday client")
    group_id: Optional[str] = Field(None, description="ID of the group")
    parent_item_id: Optional[str] = Field(None, description="ID of the item if it exists")
    columns_values: Optional[dict] = Field(None, description="Name of the columns")

class CreateUpdateItemParams(BaseModel):
    """Parameters for creating a comment/update on an item."""
      
    board_id: Optional[str] = Field(..., description="ID of the board")
    item_id: Optional[str] = Field(..., description="Kind of board to create")
    monday_client: str = Field(..., description="Monday client")
    columns_values: Optional[dict] = Field(None, description="Values of the columns")

#class CreateDocParams(BaseModel):
#    """Parameters for creating a new document."""
#
#    monday_client: str = Field(..., description="Monday client")
#    board_name: Optional[str] = Field(None, description="Name of the board")
#    board_king: Optional[str] = Field("public", description="The kind of board to create")

#monday-list-boards: Lists all available Monday.com boards
#monday-list-items-in-groups: Lists all items in specified groups of a Monday.com board
#monday-list-subitems-in-items: Lists all sub-items for given Monday.com items

class ListBoardsParams(BaseModel):
    """Parameters for listing boards."""

    limit: int = Field(10, description="Maximum number of boards to return")
    offset: int = Field(0, description="Offset for pagination")
    active: Optional[bool] = Field(None, description="Filter by active status")
    user: Optional[str] = Field(None, description="Filter by user")
    query: Optional[str] = Field(
        None,
        description="Case-insensitive search term that matches against board or other fields. Uses Monday's LIKE operator for partial matching.",
    )

class ListItemsInGroups(BaseModel):
    """Parameters for listing items in groups."""

    limit: int = Field(10, description="Maximum number of items to return")
    offset: int = Field(0, description="Offset for pagination")
    active: Optional[bool] = Field(None, description="Filter by active status")
    group: Optional[str] = Field(None, description="Filter by group")
    board: Optional[str] = Field(None, description="Filter by board")
    query: Optional[str] = Field(
        None,
        description="Case-insensitive search term that matches against group, board or other fields. Uses Monday's LIKE operator for partial matching.",
    )

class ListSubitems(BaseModel):
    """Parameters for listing subitems."""

    limit: int = Field(10, description="Maximum number of subitems to return")
    offset: int = Field(0, description="Offset for pagination")
    active: Optional[bool] = Field(None, description="Filter by active status")
    item: Optional[str] = Field(None, description="Filter by item")
    group: Optional[str] = Field(None, description="Filter by group")
    board: Optional[str] = Field(None, description="Filter by board")
    query: Optional[str] = Field(
        None,
        description="Case-insensitive search term that matches against group, board or other fields. Uses Monday's LIKE operator for partial matching.",
    )

#monday-get-board-groups: Retrieves all groups from a specified Monday.com board
#monday-get-item-updates: Retrieves updates/comments for a specific item
#monday-get-docs: Lists documents in Monday.com, optionally filtered by folder
#monday-get-doc-content: Retrieves the content of a specific document    

class GetGroupByNumberParams(BaseModel):
    """Parameters for fetching an group by its number."""

    group_number: str = Field(..., description="The number of the group to fetch")

#monday-add-doc-block: Adds a block to an existing document
#monday-move-item-to-group: Moves a Monday.com item to a different group
#monday-archive-item: Archives a Monday.com item
#monday-delete-item: Deletes a Monday.com item

class DeleteItemParams(BaseModel):
    """Parameters for deleting an item from a board"""
  
    monday_client: str = Field(..., description="Monday client")
    item_id: str = Field(..., description="ID of the item to delete")
   
