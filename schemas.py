from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ResponseMessageModel(BaseModel):
    message: str
    type: str = "text"

class OutputModel(BaseModel):
    status: str = Field(default="success")
    invocationId: str
    response: List[ResponseMessageModel]

#-----------------------------------------------------------------------------------------------------------------
#-----------------------CREATE------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------    

# 1 - monday-create-board: Creates a new Monday.com board
class CreateBoardParams(BaseModel):
    board_name: str
    board_kind: str

# 2 - monday-create-board-group: Creates a new group in a Monday.com board
class CreateBoardGroupParams(BaseModel):
    board_id: str
    group_name: str

# 3 - monday-create-item: Creates a new item in a Monday.com board
class CreateItemParams(BaseModel):
    item_name: str
    board_id: str
    group_id: str
    column_values: Optional[dict] = None
    create_labels_if_missing: bool = False

# 22 - monday-create-subitem: Creates a new subitem in a Monday.com item
class CreateSubitemParams(BaseModel):
    subitem_name: str
    parent_item_id: str = None
    column_values: Optional[dict] = None
    create_labels_if_missing: bool = False

# 4 - monday-create-update: Creates a comment/update on a Monday.com item
class CreateUpdateCommentParams(BaseModel):
    item_id: str
    update_value: str

# 5 - monday-create-doc: Creates a new document in Monday.com 
class CreateDocParams(BaseModel):
    title: str
    workspace_id: Optional[str] = None
    board_id: Optional[str] = None
    kind: Optional[str] = None
    column_id: Optional[str] = None
    item_id: Optional[str] = None 

# 27 - monday-create-doc-by-workspace: Creates a new document by workspace in Monday.com 
class CreateDocWorkspaceParams(BaseModel):
    title: str
    workspace_id: str
    kind: str

# 28 - monday-create-doc-item-column: Creates a new document by item and column in Monday.com 
class CreateDocItemParams(BaseModel):
    title: str
    column_id: str
    item_id: str

# 23 -  monday-create-column: Crea a Monday.com column
class CreateColumnParams(BaseModel):
    board_id:str
    column_title:str
    column_type: Optional[str] = None
    defaults: Optional[Dict[str, Any]] = None    

#-----------------------------------------------------------------------------------------------------------------  
#-----------------------LIST--------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------- 

# 6 - monday-list-boards: Lists all available Monday.com boards
class ListBoardsParams(BaseModel):
    limit: int
    page: int

# 7 - monday-get-board-groups: Retrieves all groups from a specified Monday.com board 
class GetBoardGroupsParams(BaseModel):
    board_id: str     

# 8 - monday-list-items-in-groups: Lists all items in specified groups of a Monday.com board
class ListItemsInGroupsParams(BaseModel):
    board_id: str
    group_ids: List[str]
    limit: Optional[int] = 25
    cursor: Optional[str] = None    

# 9 - monday-list-subitems-in-items: Lists all sub-items for given Monday.com items
class ListSubitemsParams(BaseModel): 
    #workspace_id: int
    item_ids: List[str]

# 10 - monday-get-item-updates: Retrieves updates/comments for a specific item
class GetItemUpdatesParams(BaseModel):
    item_id: str 
    limit: int    

# 11 - monday-get-docs: Lists documents in Monday.com, optionally filtered by folder
class GetDocsParams(BaseModel):
    limit: int = 20  

# 12 - monday-get-doc-content: Retrieves the content of a specific document
class GetDocContentParams(BaseModel):
    doc_id: str

# 25 - monday-list-workspaces: Lists all available Monday.com workspaces

#----------------------------------------------------------------------------------------------------------------- 
#-----------------------GET---------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------- 

# 13 - monday-list-users: Lists all available Monday.com users

# 14 - monday-get-item-by-id: Retrieves items by theirs IDs
class GetItemByIdParams(BaseModel):
    items_id: List[str] 

# 15 - monday-get-board-columns: Get the Columns of a Monday.com Board
class GetBoardColumnsParams(BaseModel):
    board_id: str 



#----------------------------------------------------------------------------------------------------------------- 
#-----------------------UPDATE------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------- 

# 16 - monday-update-item: Update a Monday.com item's or sub-item's column values.   
class UpdateItemParams(BaseModel):
    board_id: str
    item_id: str
    column_values: dict[str,Any] 
    create_labels_if_missing: bool    

# 17 - monday-move-item-to-group: Moves a Monday.com item to a different group
class MoveItemToGroup(BaseModel):
    item_id:str
    group_id:str

# 18 - monday-archive-item: Archives a Monday.com item
class ArchiveItemParams(BaseModel):
    item_id: str   

# 19 - monday-add-doc-block: Adds a block to an existing document
class AddDocBlockParams(BaseModel):                 
    doc_id: str
    block_type: str
    content: str
    after_block_id: Optional[str] = None   


#----------------------------------------------------------------------------------------------------------------- 
#-----------------------DELETE------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------- 

# 20 - monday-delete-group: Deletes a Monday.com group
class DeleteGroupByIdParams(BaseModel):
    board_id:  str
    group_id: str

# 21 - monday-delete-item: Deletes a Monday.com item
class DeleteItemByIdParams(BaseModel):
    item_id:str

# 24 - monday-delete-column: Deletes a Monday.com column
class DeleteColumnByIdParams(BaseModel):
    board_id:  str
    column_id: str

#----------------------------------------------------------------------------------------------------------------- 
#-----------------------OTHERS------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------- 


class FetchItemsByBoardId(BaseModel):
    board_id:str

class columnType(BaseModel):
    value:str 

# 26 - monday-import-info-from-excel: Read excel and create board, group, item, subitem, column containing information from excel rows on Monday.com 
class OpenExcel(BaseModel):
    file_name:str
    download:Optional[str] = "True"
    rows:Optional[int] = 0
    uid:Optional[str] = None
    continuar:Optional[str] = "False"
    esperar:Optional[str] = "True"

class ProcessExcelStatus(BaseModel):
    detener:Optional[str] = "False"
    purgar_inactivos:Optional[str] = "False"
    purgar_procesos_antiguos:Optional[str] = "False"
    uid:Optional[str] = None
    
    
   
