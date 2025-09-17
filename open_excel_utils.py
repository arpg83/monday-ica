import pandas as pd
import logging
from monday import MondayClient
from monday.resources.types import BoardKind
import requests
import os
import time
import shutil
import json

logger = logging.getLogger(__name__)

class AnalisisItem():
    row_inicio:int
    row_fin:int
    max_outline:int
    item_name:str

    def __init__(self):
        self.row_inicio = 0
        self.row_fin = 0
    
    def get_log(self):
        """Genera linea de log"""
        return f"item: {self.item_name} max_outline: {self.max_outline} inicio:{self.row_inicio +1} fin:{self.row_fin +1}"

class ExcelUtilsMonday:
    local_filename = ""
    uid = ""
    download:bool = False
    eliminado_grupo_inicial = False
    board_id = None
    group_id = None
    item_id_l1 = None
    item_id_l2 = None
    item_id_l3 = None
    item_id_l4 = None
    item_id_l5 = None
    pos = 0
    wait_time = 1
    esperar = True
    proceso_completo = False
    error = False
    message = ""
    continuar:bool = False

    def __init__(self):
        self.download = False
        self.eliminado_grupo_inicial = False

    def clean_files(self):
        """Limpia los archivos"""
        if self.proceso_completo:
            logger.info("Eliminando")
            logger.info(self.local_filename)
            if os.path.exists(self.local_filename):
                os.remove(self.local_filename)
            logger.info(self.get_local_uid_path(self.uid))
            #Borrar data.json
            data_json = f'{self.get_local_uid_path(self.uid)}/data.json'
            if os.path.exists(data_json):
                os.remove(data_json)
            os.rmdir(self.get_local_uid_path(self.uid))

    def get_local_uid_path(self,uid = None):
        """Obtiene el path desde el uid"""
        dir_procesa = 'procesa_archivos'
        if not os.path.exists(dir_procesa):
            os.mkdir(dir_procesa)
        dir_uid = f"{dir_procesa}/{uid}"
        if not os.path.exists(dir_uid):
            os.mkdir(dir_uid)
        return dir_uid

    def get_local_fileName(self,uid = None,filename = "archivo.xlsx"):
        """Obtiene el path del archivo local"""
        dir_uid = self.get_local_uid_path(uid)
        return f"{dir_uid}/{filename}"

    def download_file(self,url, local_filename):
        """Descarga un archivo desde internet"""
        with requests.get(url, stream=True,timeout=30) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
        self.local_filename = local_filename
        return local_filename

    def get_file(self,uid,filename):
        """descarga el archivo"""
        if self.continuar and os.path.exists(self.local_filename):
            return self.local_filename
        else:
            file_path = filename
            self.uid = uid
            if self.download:
                file_path= self.get_local_fileName(uid,"archivo.xlsx")
                
                self.download_file(filename,file_path)
                logger.info(f"descarga {filename} {file_path}")
            else:
                file_path= self.get_local_fileName(uid,"archivo.xlsx")
                shutil.copy(filename,file_path)
            self.local_filename = file_path
            return self.local_filename

    def get_pandas(self,filename,download=False,uid = None):
        """Procesa obtiene un pandas dataframe de una url o un archivo local"""
        if download:
            self.download = True
        file_path = self.get_file(uid,filename)

        logger.info(f"abriendo:{file_path}")
        df = pd.read_excel(file_path)
        logger.info(f"Retorna pandas:{file_path}")
        #logger.info(df)
        #logger.info(df.columns.values)
        return df

    def list_columns(self,df:pd.DataFrame):
        """lista columnas del documento pandas/excel"""
        return df.columns.values

    def read_cell(self,df:pd.DataFrame,column_name,row_id):
        """Lee una celda especifica"""
        arr_cols = df.columns.values
        index_col = 0
        for index,col in enumerate(arr_cols):
            logger.debug(index)
            logger.debug(col)
            if col == column_name:
                index_col = index
        logger.debug(row_id)
        logger.debug(index_col)
        return df.iloc[row_id,index_col]

    def salvar_estado(self,error=False):
        """Salva el estado del proceso en un archivo json data.json"""
        data = {
            "board_id":self.board_id,
            "group_id":self.group_id,
            "item_id":self.item_id_l1,
            "pos":self.pos,
            "error":error,
            "message":str(self.message),
            "local_filename":str(self.local_filename)
        }
        text_json = json.dumps(data)
        logging.info(text_json)
        with open(f'{self.get_local_uid_path(self.uid)}/data.json', 'w') as outfile:
            json.dump(data, outfile)

    def read_estado(self):
        """Recupera el estado del proceso del archivo json data.json"""
        with open(f'{self.get_local_uid_path(self.uid)}/data.json', 'r') as input:
            data = json.load(input)
        self.board_id = data["board_id"]
        self.group_id = data["group_id"]
        self.item_id_l1 = data["item_id"]
        self.pos = data["pos"]
        self.error = bool(data["error"])
        self.local_filename = data["local_filename"]
        logger.info("Fin de proceso")
        logger.info(self.board_id)
        logger.info(self.group_id)
        logger.info(self.item_id_l1)
        logger.info(self.pos)
        logger.info(self.error)
        logger.info(self.local_filename)

    def identify_type(self,outline_lvl):
        """Identifica si la fila es un board, grupo, item o subitem"""
        if str(outline_lvl).strip() == '1':
            return 'board'
        if str(outline_lvl).strip() == '2':
            #return 'board'
            return 'group'
        if str(outline_lvl).strip() == '3':
            #return 'group'
            return 'item'
        if str(outline_lvl).strip() == '4':
            #return 'item'
            return 'subiteml1'
#        if str(outline_lvl).strip() == '5':
#            return 'subiteml1'
            #return 'subiteml2'#column
#        if str(outline_lvl).strip() == '6':
#            return 'subiteml3'#column
#        if str(outline_lvl).strip() == '7':
#            return 'subiteml4'#column
        return 'undefined'
    

    def process_excel_monday(self,filename, download , monday_client:MondayClient,uid = None,rows=0,continuar = False):
        """Procesa el excel de monday si se le da una url asignar el parametro download = True, si se desea procesar una cantidad limitada de filas asignar un valor a rows si el valor es 0 procesara todo el documento"""
        self.continuar = continuar
        #Actualmente sobrescribe el archivo si continua
        df = self.get_pandas(filename,download,uid)
        logger.info(self.list_columns(df))
        logger.info(uid)
        cant_total_filas = len(df.index)
        cantidad_a_procesar = 0
        if rows == 0:
            cantidad_a_procesar = cant_total_filas
        if continuar:
            logger.info("Continua proceso")
            self.read_estado()
        if continuar and rows != 0:
            cantidad_a_procesar = self.pos + rows + 1
            if cantidad_a_procesar >= cant_total_filas:
                cantidad_a_procesar = cant_total_filas
        if not continuar:
            self.pos = 0
        logger.info(f"se procesaran {rows} {self.pos} de {cantidad_a_procesar} registros")
        if continuar:
            if self.error:
                self.pos = self.pos -1 # Si termino en estado de error retomo desde el ultimo registro que no se pudo procesar

            self.eliminado_grupo_inicial = True # Seteo en verdadero que el grupo inicial fue eliminado para que no dispare el error de que el grupo inicial no existe
            self.error = False
        logger.info("Cantidad de rows:")
        logger.info(cantidad_a_procesar)
        try:
            for i in range(cantidad_a_procesar):
                if not continuar or (continuar and i > self.pos):
                    self.pos = i
                    title = self.read_cell(df,"Name",i)
                    outline_lvl = self.read_cell(df,"Outline Level",i)
                    message = f"Row: {i}"
                    logger.info(message)
                    logger.info(title)
                    logger.info(outline_lvl)
                    logger.info(self.identify_type(outline_lvl))
                    if self.identify_type(outline_lvl) == 'board':
                        self.board_id = self.xls_create_board(monday_client,title,'public')
                    if self.identify_type(outline_lvl) == 'group':
                        self.group_id = self.xls_create_group(monday_client,title,self.board_id)
                    if self.identify_type(outline_lvl) == 'item':
                        self.item_id_l1 = self.xls_create_item(monday_client,title,self.board_id,self.group_id)
                    if self.identify_type(outline_lvl) == 'subiteml1':
                        self.item_id_l2 = self.xls_create_sub_item(monday_client,title,self.item_id_l1)
                    if self.identify_type(outline_lvl) == 'subiteml2':
                        self.item_id_l3 = self.xls_create_sub_item(monday_client,title,self.item_id_l1)
                    if self.identify_type(outline_lvl) == 'subiteml3':
                        self.item_id_l4 = self.xls_create_sub_item(monday_client,title,self.item_id_l1)
                    if self.identify_type(outline_lvl) == 'subiteml4':
                        self.item_id_l5 = self.xls_create_sub_item(monday_client,title,self.item_id_l1)
                    if self.esperar:
                        time.sleep(self.wait_time)  # Pauses execution for 3 seconds.
        except Exception as e:
            self.error = True
            self.message = e
            logger.error(e)
        logger.info("Fin de proceso")
        logger.info(self.board_id)
        logger.info(self.group_id)
        logger.info(self.item_id_l1)
        logger.info(self.pos)
        if cant_total_filas == rows:
            self.proceso_completo = True
        self.salvar_estado(self.error)
        self.clean_files()

    def limpiar_nombre(self,texto:str):
        """Limpia el texto de un titulo"""
        texto_con_escapeo = str(texto).replace("\\","\\\\")
        texto_con_escapeo = str(texto_con_escapeo).replace("\"","\\\"")
        return texto_con_escapeo
        #return json.dumps(texto)

    def xls_create_board(self,monday_client:MondayClient,board_name,board_kind):
        """Crea un board"""
        text = f"Create board: {board_name} {board_kind}"
        logger.info(text)

        #Crear logica de reintento
        actual_board_kind = BoardKind(board_kind)
        respuesta = monday_client.boards.create_board(
            board_name= self.limpiar_nombre(board_name)
            ,board_kind= actual_board_kind
            )
        logger.info(respuesta)
        board_id = respuesta['data']['create_board']['id']
        #Resetea el flag de borrado de grupo inicial
        self.eliminado_grupo_inicial = False
        return  board_id
            

    def xls_create_group(self,monday_client:MondayClient,group_name,board_id):
        """Crea un grupo"""
        text = f"Create group: {group_name} {board_id}"
        logger.info(text)
        
        #Crear logica de reintento
        respuesta = monday_client.groups.create_group(
            group_name= self.limpiar_nombre(group_name),
            board_id=board_id
        )
        logger.info(respuesta)

        group_id = respuesta['data']['create_group']['id']

        if not self.eliminado_grupo_inicial:
            #Crear logica de reintento
            respuesta2 = monday_client.groups.delete_group(
                board_id=board_id
                ,group_id='topics'
            )
            logger.info(respuesta2)
            self.eliminado_grupo_inicial = True

        return  group_id


    def xls_create_item(self,monday_client:MondayClient,item_name,board_id,group_id):
        """Crea un item"""
        text = f"Create Item: {item_name} {board_id} {group_id}"
        logger.info(text)
        #Crear logica de reintento
        respuesta = monday_client.items.create_item(
            item_name= self.limpiar_nombre(item_name)
            ,board_id=board_id
            ,group_id=group_id
            ,column_values= {"checkbox":{"checked":True}}
            ,create_labels_if_missing=True
            #{"date":"2023-05-25"}
        )
        logger.info(respuesta)
        item_id = respuesta['data']['create_item']['id']
        logger.info(item_id)
        return item_id

    def xls_create_sub_item(self,monday_client:MondayClient,item_name,item_id):
        """Crea un subitem"""
        text = f"Create sub item: {item_name} {item_id}"
        logger.info(text)


        respuesta = monday_client.items.create_subitem(
            subitem_name = self.limpiar_nombre(item_name)
            ,parent_item_id = item_id
            #,column_values=  json.dumps({"date0":"2023-05-25"})
            #,create_labels_if_missing=True
        )
        logger.info(respuesta)
        item_id = respuesta['data']['create_subitem']['id']
        logger.info(item_id)
        return  item_id
    
    def analizar_excel(self,filename, download ,uid = None):
        df = self.get_pandas(filename,download,uid)
        cant_total_filas = len(df.index)
        analisis_item = AnalisisItem()
        primer_item = True
        arr_analisis_items = []
        for i in range(cant_total_filas):
            self.pos = i
            title = self.read_cell(df,"Name",i)
            outline_lvl = self.read_cell(df,"Outline Level",i)
            tipo = self.identify_type(outline_lvl)
            logger.debug(tipo)
            logger.debug(outline_lvl)
            if tipo == 'item':
                if not primer_item and analisis_item.max_outline > 4:
                    analisis_item.row_fin = i -1
                    arr_analisis_items.append(analisis_item)
                analisis_item = AnalisisItem()
                analisis_item.row_inicio = i
                primer_item = False
                analisis_item.item_name = title
                analisis_item.max_outline = int(outline_lvl)
            else:
                if not primer_item and int(analisis_item.max_outline) < int(outline_lvl):
                    analisis_item.max_outline = int(outline_lvl)
        for obj in arr_analisis_items:
            analisis:AnalisisItem = obj
            logger.debug(analisis.get_log())
        self.proceso_completo = True
        self.clean_files()
        return arr_analisis_items