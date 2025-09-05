import pandas as pd
import logging
from monday import MondayClient
from monday.resources.types import BoardKind

logger = logging.getLogger(__name__)

def get_pandas(filename,download=False):
    """Procesa obtiene un pandas dataframe de una url o un archivo local"""
    if download == True:
        logger.info(f"descarga {filename}")
    logger.info(f"abriendo:{filename}")
    df = pd.read_excel(filename)
    logger.info(f"Retorna pandas:{filename}")
    #logger.info(df)
    #logger.info(df.columns.values)
    return df

def list_columns(df:pd.DataFrame):
    return df.columns.values

def read_cell(df:pd.DataFrame,column_name,row_id):
    arrCols = df.columns.values
    index_col = 0
    for index,col in enumerate(arrCols):
        logger.debug(index)
        logger.debug(col)
        if col == column_name:
            index_col = index
    logger.debug(row_id)
    logger.debug(index_col)
    return df.iloc[row_id,index_col]

def identify_type(outline_lvl):
    if str(outline_lvl).strip() == '1':
        return 'board'
    if str(outline_lvl).strip() == '2':
        return 'group'
    if str(outline_lvl).strip() == '3':
        return 'item'
    if str(outline_lvl).strip() == '4':
        return 'subiteml1'
    if str(outline_lvl).strip() == '5':
        return 'subiteml2'
    if str(outline_lvl).strip() == '6':
        return 'subiteml3'
    if str(outline_lvl).strip() == '7':
        return 'subiteml4'
    return 'undefined'

def process_excel_monday(filename, download , monday_client:MondayClient,simulacion = False):
    df = get_pandas(filename,download)
    logger.info(list_columns(df))

    board_id = None
    group_id = None
    item_id_l1 = None
    item_id_l2 = None
    item_id_l3 = None
    item_id_l4 = None
    
    for i in range(30):
        title = read_cell(df,"Name",i)
        outline_lvl = read_cell(df,"Outline Level",i)
        message = f"Row: {i}"
        logger.info(message)
        logger.info(title)
        logger.info(outline_lvl)
        logger.info(identify_type(outline_lvl))
        if identify_type(outline_lvl) == 'board':
            board_id = xls_create_board(monday_client,title,'public',simulacion)
        if identify_type(outline_lvl) == 'group':
            group_id = xls_create_group(monday_client,title,board_id,simulacion)
        if identify_type(outline_lvl) == 'item':
            item_id_l1 = xls_create_item(monday_client,title,board_id,group_id,simulacion)
        if identify_type(outline_lvl) == 'subiteml1':
            item_id_l2 = xls_create_sub_item(monday_client,title,item_id_l1,simulacion)
        if identify_type(outline_lvl) == 'subiteml2':
            item_id_l3 = xls_create_sub_item(monday_client,title,item_id_l1,simulacion)
        if identify_type(outline_lvl) == 'subiteml3':
            item_id_l4 = xls_create_sub_item(monday_client,title,item_id_l1,simulacion)


def xls_create_board(monday_client:MondayClient,board_name,board_kind,simulacion:bool):
    text = f"Create board: {board_name} {board_kind}"
    logger.info(text)

    if simulacion:
        board_id = 9986350370
        return board_id
    else:
        actual_board_kind = BoardKind(board_kind)
        respuesta = monday_client.boards.create_board(
            board_name= board_name
            ,board_kind= actual_board_kind
            )
        logger.info(respuesta)
        return  respuesta['data']['create_board']['id']
        

def xls_create_group(monday_client:MondayClient,group_name,board_id,simulacion:bool):
    text = f"Create group: {group_name} {board_id}"
    logger.info(text)
    
    if simulacion:
        group_id = 'group_mkvg7rfr'
        return group_id
    else:
        respuesta = monday_client.groups.create_group(
            group_name=group_name,
            board_id=board_id
        )
        logger.info(respuesta)
        return  respuesta['data']['create_group']['id']


def xls_create_item(monday_client:MondayClient,item_name,board_id,group_id,simulacion:bool):
    text = f"Create Item: {item_name} {board_id} {group_id}"
    logger.info(text)

    if simulacion:
        item_id = 0
        return item_id
    else:
        respuesta = monday_client.items.create_item(
            item_name= item_name
            ,board_id=board_id
            ,group_id=group_id
        )
        item_id = respuesta['data']['create_item']['id']
        logger.info(item_id)
        return item_id

def xls_create_sub_item(monday_client:MondayClient,item_name,item_id,simulacion:bool):
    text = f"Create sub item: {item_name} {item_id}"
    logger.info(text)

    if simulacion:
        item_id = 0
        return item_id
    else:
        respuesta = monday_client.items.create_subitem(
            subitem_name = item_name
            ,parent_item_id = item_id
        )
        return  respuesta['data']['create_subitem']['id']