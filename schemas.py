from pydantic import BaseModel, Field
from typing import Optional, List

class ResponseMessageModel(BaseModel):
    message: str
    type: str = "text"

class OutputModel(BaseModel):
    status: str = Field(default="success")
    invocationId: str
    response: List[ResponseMessageModel]

#monday-create-board: Creates a new Monday.com board
class CreateBoardParams(BaseModel):
    board_name: str
    board_kind: str

#monday-create-board-group: Creates a new group in a Monday.com board
class CreateBoardGroupParams(BaseModel):
    board_id: str
    group_name: str

#monday-create-item: Creates a new item or sub-item in a Monday.com board
class CreateItemParams(BaseModel):
    item_name: str
    board_id: Optional[str] = None
    group_id: Optional[str] = None
    parent_item_id: Optional[str] = None
    column_values: Optional[dict] = None

#monday-create-update: Creates a comment/update on a Monday.com item
class CreateUpdateCommentParams(BaseModel):
    item_id: str
    update_text: str

#monday-update-item: Update a Monday.com item's or sub-item's column values.   
class UpdateItemParams(BaseModel):
    board_id: str
    item_id: str
    #monday_client: str
    #column_values: List[str]
    column_values: dict

#monday-create-doc: Creates a new document in Monday.com 
class CreateDocParams(BaseModel):
    title: str
    workspace_id: int
    kind: str
    board_id: str
    column_id: str
    item_id: int    

#monday-list-boards: Lists all available Monday.com boards
class ListBoardsParams(BaseModel):
    limit: int
    page: int

#monday-list-items-in-groups: Lists all items in specified groups of a Monday.com board
class ListItemsInGroups(BaseModel): 
    #monday_client: str 
    board_id: str 
    group_ids: List[str] 
    limit: int
    cursor: str

#monday-list-subitems-in-items: Lists all sub-items for given Monday.com items
class ListSubitems(BaseModel): 
    #workspace_id: int
    item_ids: List[str]

#monday-get-board-groups: Retrieves all groups from a specified Monday.com board 
class GetBoardGroupsParams(BaseModel):
    board_id: str 

#monday-get-item-updates: Retrieves updates/comments for a specific item
class GetItemUpdatesParams(BaseModel):
    item_id: str 
    limit: int    

#monday-get-docs: Lists documents in Monday.com, optionally filtered by folder
class GetDocsParams(BaseModel):
    limit: int  

#monday-get-doc-content: Retrieves the content of a specific document
class GetDocContentParams(BaseModel):
    doc_id: str          

class GetGroupByNumberParams(BaseModel):
    group_number: str 

class GetItemByIdParams(BaseModel):
    item_id: str   

#monday-add-doc-block: Adds a block to an existing document
class AddDocBlockParams(BaseModel):                 
    doc_id: str
    block_type: str
    content: str
    after_block_id: str 

#monday-move-item-to-group: Moves a Monday.com item to a different group
class MoveItemToGroupId(BaseModel):
    item_id:str
    group_id:str

#monday-archive-item: Archives a Monday.com item
class ArchiveItemParams(BaseModel):
    item_id: str         

class FetchItemsByBoardId(BaseModel):
    board_id:str

#monday-delete-item: Deletes a Monday.com item
class DeleteItemByIdParams(BaseModel):
    item_id:str

class MoveItemToGroupId(BaseModel):
    item_id:str
    group_id:str

class GetItemComentsParams(BaseModel):
    item_id:str
    limit:int

class GetItemById(BaseModel):
    items_id:str

class columnType(BaseModel):
    value:str

class CreateColumn(BaseModel):
    board_id:str
    column_title:str
    column_type:columnType
    defaults: Optional[object] = None
