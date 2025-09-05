import pandas as pd
import logging
from monday import MondayClient

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

def process_excel_monday(filename, download , monday_client):
    df = get_pandas(filename,download)
    logger.info(list_columns(df))
    for i in range(30):
        title = read_cell(df,"Name",i)
        outline_lvl = read_cell(df,"Outline Level",i)
        logger.info(title)
        logger.info(outline_lvl)
        logger.info(identify_type(outline_lvl))
        board_id = None
        group_id = None
        item_id_l1 = None
        item_id_l2 = None
        item_id_l3 = None
        item_id_l4 = None
        if identify_type(outline_lvl) == 'board':
            board_id = xls_create_board(monday_client,title,'public')
        if identify_type(outline_lvl) == 'group':
            group_id = xls_create_group(monday_client,title,board_id)
        if identify_type(outline_lvl) == 'item':
            item_id_l1 = xls_create_item(monday_client,title,board_id,group_id)
        if identify_type(outline_lvl) == 'subiteml1':
            item_id_l2 = xls_create_sub_item(monday_client,title,item_id_l1)
        if identify_type(outline_lvl) == 'subiteml2':
            item_id_l3 = xls_create_sub_item(monday_client,title,item_id_l2)
        if identify_type(outline_lvl) == 'subiteml3':
            item_id_l4 = xls_create_sub_item(monday_client,title,item_id_l3)

def xls_create_group(monday_client,group_name,board_id):
    text = f"Create group: {group_name} {board_id}"
    logger.info(text)
    
    group_id = 0
    return group_id

def xls_create_board(monday_client,board_name,board_kind):
    text = f"Create board: {board_name} {board_kind}"
    logger.info(text)

    board_id = 0
    return board_id

def xls_create_item(monday_client,item_name,board_id,group_id):
    text = f"Create Item: {item_name} {board_id} {group_id}"
    logger.info(text)

    item_id = 0
    return item_id

def xls_create_sub_item(monday_client,item_name,item_id):
    text = f"Create sub item: {item_name} {item_id}"
    logger.info(text)

    item_id = 0
    return item_id