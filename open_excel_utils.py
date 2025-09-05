import pandas as pd
import logging

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
        return 'subitem'
    if str(outline_lvl).strip() == '5':
        return 'subitem'
    return 'undefined'

def process_excel_monday(filename,download=False):
    df = get_pandas(filename,download)
    logger.info(list_columns(df))
    for i in range(5):
        title = read_cell(df,"Name",i)
        outline_lvl = read_cell(df,"Outline Level",i)
        logger.info(title)
        logger.info(outline_lvl)
        logger.info(identify_type(outline_lvl))
        board_id = 0
        if identify_type(outline_lvl) == 'board':
            board_id = xls_create_board(title,'public')
        if identify_type(outline_lvl) == 'group':
            board_id = xls_create_group(title,board_id)

def xls_create_group(group_name,board_id):
    text = f"Create group: {group_name} {board_id}"
    logger.info(text)
    
    group_id = 0
    return group_id

def xls_create_board(board_name,board_kind):
    text = f"Create board: {board_name} {board_kind}"
    logger.info(text)

    board_id = 0
    return board_id