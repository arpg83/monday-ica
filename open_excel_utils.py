import pandas as pd
import logging
from monday import MondayClient
from monday.resources.types import BoardKind
import requests
import os
import time

logger = logging.getLogger(__name__)

class ExcelUtilsMonday:
    local_filename = ""
    uid = ""
    dwnload:bool = False
    eliminado_grupo_inicial = False

    def __init__(self):
        self.download = False
        self.eliminado_grupo_inicial = False

    def clean_files(self):
        if self.dwnload:
            os.remove(self.local_filename)
            os.remove(self.get_local_uid_path(self.uid))

    def get_local_uid_path(self,uid = None):
        dir_procesa = 'procesa_archivos'
        if not os.path.exists(dir_procesa):
            os.mkdir(dir_procesa)
        dir_uid = f"{dir_procesa}/{uid}"
        if not os.path.exists(dir_uid):
            os.mkdir(dir_uid)
        return dir_uid

    def get_local_fileName(self,uid = None):
        dir_uid = self.get_local_uid_path(uid)
        return f"{dir_uid}/archivo.xlsx"

    def download_file(self,url, local_filename):
        """Descarga un archivo desde internet"""
        with requests.get(url, stream=True,timeout=30) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
        self.local_filename = local_filename
        return local_filename

    def get_pandas(self,filename,download=False,uid = None):
        """Procesa obtiene un pandas dataframe de una url o un archivo local"""
        file_path = filename
        if download == True:
            file_path= self.get_local_fileName(uid)
            self.uid = uid
            self.dwnload = True
            self.download_file(filename,file_path)
            logger.info(f"descarga {filename} {file_path}")

        logger.info(f"abriendo:{file_path}")
        df = pd.read_excel(file_path)
        logger.info(f"Retorna pandas:{file_path}")
        #logger.info(df)
        #logger.info(df.columns.values)
        return df

    def list_columns(self,df:pd.DataFrame):
        return df.columns.values

    def read_cell(self,df:pd.DataFrame,column_name,row_id):
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

    def identify_type(self,outline_lvl):
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

    def process_excel_monday(self,filename, download , monday_client:MondayClient,uid = None,rows=0,simulacion = False):
        """Procesa el excel de monday si se le da una url asignar el parametro download = True, si se desea procesar una cantidad limitada de filas asignar un valor a rows si el valor es 0 procesara todo el documento"""
        df = self.get_pandas(filename,download,uid)
        logger.info(self.list_columns(df))
        logger.info(uid)

        board_id = None
        group_id = None
        item_id_l1 = None
        item_id_l2 = None
        item_id_l3 = None
        item_id_l4 = None
        if rows == 0:
            rows = len(df.index)
        for i in range(rows):
            title = self.read_cell(df,"Name",i)
            outline_lvl = self.read_cell(df,"Outline Level",i)
            message = f"Row: {i}"
            logger.info(message)
            logger.info(title)
            logger.info(outline_lvl)
            logger.info(self.identify_type(outline_lvl))
            if self.identify_type(outline_lvl) == 'board':
                board_id = self.xls_create_board(monday_client,title,'public',simulacion)
            if self.identify_type(outline_lvl) == 'group':
                group_id = self.xls_create_group(monday_client,title,board_id,simulacion)
            if self.identify_type(outline_lvl) == 'item':
                item_id_l1 = self.xls_create_item(monday_client,title,board_id,group_id,simulacion)
            if self.identify_type(outline_lvl) == 'subiteml1':
                item_id_l2 = self.xls_create_sub_item(monday_client,title,item_id_l1,simulacion)
            if self.identify_type(outline_lvl) == 'subiteml2':
                item_id_l3 = self.xls_create_sub_item(monday_client,title,item_id_l1,simulacion)
            if self.identify_type(outline_lvl) == 'subiteml3':
                item_id_l4 = self.xls_create_sub_item(monday_client,title,item_id_l1,simulacion)
            time.sleep(3)  # Pauses execution for 3 seconds.
        self.clean_files()

    def xls_create_board(self,monday_client:MondayClient,board_name,board_kind,simulacion:bool):
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
            board_id = respuesta['data']['create_board']['id'] 
            return  board_id
            

    def xls_create_group(self,monday_client:MondayClient,group_name,board_id,simulacion:bool):
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

            group_id = respuesta['data']['create_group']['id']

            if not self.eliminado_grupo_inicial:
                respuesta2 = monday_client.groups.delete_group(
                    board_id=board_id
                    ,group_id='topics'
                )
                logger.info(respuesta2)
                self.eliminado_grupo_inicial = True

            return  group_id


    def xls_create_item(self,monday_client:MondayClient,item_name,board_id,group_id,simulacion:bool):
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
            logger.info(respuesta)
            item_id = respuesta['data']['create_item']['id']
            logger.info(item_id)
            return item_id

    def xls_create_sub_item(self,monday_client:MondayClient,item_name,item_id,simulacion:bool):
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
            logger.info(respuesta)
            item_id = respuesta['data']['create_subitem']['id']
            logger.info(item_id)
            return  item_id