import pandas as pd
import logging
from monday import MondayClient
from monday.resources.types import BoardKind
import requests
import os

logger = logging.getLogger(__name__)

class ExcelUtilsMonday:
    local_filename = ""

    def delete_file(self):
        os.remove(self.local_filename)
        pass

    def get_local_fileName(self,filename,uid = None):
        return f"{uid}/{filename}"

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
            file_path= f"{uid}/archivo.xlsx"
            self.download_file(filename,file_path)
            logger.info(f"descarga {filename}")

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

    def process_excel_monday(self,filename, download , monday_client:MondayClient,uid = None,simulacion = False):
        
        df = self.get_pandas(filename,download,uid)
        logger.info(self.list_columns(df))

        board_id = None
        group_id = None
        item_id_l1 = None
        item_id_l2 = None
        item_id_l3 = None
        item_id_l4 = None
        
        for i in range(50):
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

            respuesta2 = monday_client.groups.delete_group(
                board_id=board_id
                ,group_id='topics'
            )
            logger.info(respuesta2)

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