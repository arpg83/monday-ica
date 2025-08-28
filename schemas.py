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
#monday-create-board-group: Creates a new group in a Monday.com board
#monday-create-item: Creates a new item or sub-item in a Monday.com board
#monday-create-update: Creates a comment/update on a Monday.com item
#monday-create-doc: Creates a new document in Monday.com    

class CreateBoardParams(BaseModel):
    board_name: str
    board_kind: str

class CreateBoardGroupParams(BaseModel):
    board_id: str
    group_name: str

class CreateItemParams(BaseModel):
    item_name: str
    board_id: Optional[str] = None
    group_id: Optional[str] = None
    parent_item_id: Optional[str] = None
    columns_values: Optional[dict] = None

#class CreateSubItemParams(BaseModel):
#    parent_item_id: Optional[str] = None
#    item_name: str
#    group_id: Optional[str] = None
#    columns_values: Optional[dict] = None

class CreateUpdateCommentParams(BaseModel):
    item_id: str
    update_text: str
    
class UpdateItemParams(BaseModel):
    board_id: str
    item_id: str
    monday_client: str
    columns_values: List[str]

class CreateDocParams(BaseModel):
    title: str
    workspace_id: int
    kind: str
    board_id: str
    column_id: str
    item_id: int    

#monday-list-boards: Lists all available Monday.com boards
#monday-list-items-in-groups: Lists all items in specified groups of a Monday.com board
#monday-list-subitems-in-items: Lists all sub-items for given Monday.com items

class ListBoardsParams(BaseModel):
    limit: int
    page: int

class ListItemsInGroups(BaseModel): 
    #monday_client: str 
    board_id: str 
    group_ids: List[str] 
    limit: int
    cursor: str

class ListSubitems(BaseModel): 
    #workspace_id: int
    item_ids: List[str]

#monday-get-board-groups: Retrieves all groups from a specified Monday.com board
#monday-get-item-updates: Retrieves updates/comments for a specific item
#monday-get-docs: Lists documents in Monday.com, optionally filtered by folder
#monday-get-doc-content: Retrieves the content of a specific document    

class GetBoardGroupsParams(BaseModel):
    board_id: str 

class GetItemUpdatesParams(BaseModel):
    item_id: str 
    limit: int    

class GetDocsParams(BaseModel):
    limit: int  

class GetDocContentParams(BaseModel):
    doc_id: str          

class GetGroupByNumberParams(BaseModel):
    group_number: str 

class GetItemByIdParams(BaseModel):
    item_id: str   

#monday-add-doc-block: Adds a block to an existing document
#monday-move-item-to-group: Moves a Monday.com item to a different group
#monday-archive-item: Archives a Monday.com item
#monday-delete-item: Deletes a Monday.com item

class AddDocBlockParams(BaseModel):                 
    doc_id: str
    block_type: str
    content: str
    after_block_id: str 

class MoveItemToGroupParams(BaseModel):                  
    item_id: str
    group_id: str

class ArchiveItemParams(BaseModel):
    item_id: str           

class DeleteItemParams(BaseModel): 
    item_id: str 
   
class FetchItemsByBoardId(BaseModel):
    board_id:str