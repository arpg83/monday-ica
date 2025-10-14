import pandas as pd
import logging
from monday import MondayClient
from monday.resources.types import BoardKind
import requests
import os
import time
import shutil
import json
from threading import Thread
from datetime import datetime,timedelta
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


class MondayItem():
    name:str
    id:str    

    def __init__(self):
        pass

class MondayGroup():
    name:str
    id:str
    items:MondayItem = []

    def __init__(self):
        pass

class MondayBoard():
    name:str
    id:str
    groups:MondayGroup = []

    def __init__(self):
        pass


class AnalisisItem():
    """Objeto para analizar y mostar la informacion de un item de monday"""
    row_inicio:int
    row_fin:int
    max_outline:int
    item_name:str

    def __init__(self):
        self.row_inicio = 0
        self.row_fin = 0
        self.max_outline = 0
        self.item_name = ""
    
    def get_log(self):
        """Genera linea de log"""
        return f"item: {self.item_name} max_outline: {self.max_outline} inicio:{self.row_inicio +1} fin:{self.row_fin +1}"


class ExcelUtilsWorks:
    """Utilidades para el directorio de procesamiento"""
    directorio:str = 'procesa_archivos'

    def __init__(self):
        pass
    def listar(self):
        """lista los uid del directorio de procesamiento"""
        arr = []
        if self.directorio is not None and os.path.exists(self.directorio):
            arr = os.listdir(self.directorio)
        return arr
    
    def purgar(self,uid):
        """Purga un uid del directorio de procesamiento"""
        excel_monday = ExcelUtilsMonday()
        excel_monday.uid = uid
        excel_monday.read_estado()
        logger.info("intenta purgar:")
        logger.info("intenta clean")
        excel_monday.proceso_completo = True
        excel_monday.clean_files()
        return True


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
    sub_board_id = None
    id_column_fecha_inicio = None
    id_column_fecha_fin = None
    id_column_crono = None
    id_column_persona = None
    id_column_responsable = None
    sub_board_id_column_fecha_inicio = None
    sub_board_id_column_fecha_fin = None
    sub_board_id_column_fecha_fin = None
    sub_board_id_column_crono = None
    sub_board_id_column_persona = None
    sub_board_id_column_responsable = None
    pos = 0
    wait_time = 1
    esperar = True
    proceso_completo = False
    error = False
    message = ""
    continuar:bool = False
    detener = False
    procesando = True
    sub_board_columns_creadas = False
    format_fecha_string = "%B %d, %Y %I:%M %p"
    #Esto permite que los niveles 5 en adelante se carguen como subitems si se setea esta variable como true
    cargar_lvl_superirores_a_como_subitems = False
    titulo_column_name = "Name"
    fecha_inicio_column_name = "Start"
    fecha_fin_column_name = "Finish"
    nivel_column_name = "Outline Level"

    def __init__(self):
        self.local_filename = ""
        self.uid = ""
        self.download:bool = False
        self.eliminado_grupo_inicial = False
        self.board_id = None
        self.group_id = None
        self.item_id_l1 = None
        self.item_id_l2 = None
        self.item_id_l3 = None
        self.item_id_l4 = None
        self.item_id_l5 = None
        self.sub_board_id = None
        self.id_column_fecha_inicio = None
        self.id_column_fecha_fin = None
        self.sub_board_id_column_fecha_inicio = None
        self.sub_board_id_column_fecha_fin = None
        self.pos = 0
        self.wait_time = 1
        self.esperar = True
        self.proceso_completo = False
        self.error = False
        self.message = ""
        self.continuar:bool = False
        self.detener = False
        self.procesando = True
        self.sub_board_columns_creadas = False
        self.format_fecha_string = "%B %d, %Y %I:%M %p"
        self.cargar_lvl_superirores_a_como_subitems = False
        self.titulo_column_name = "Name"
        self.fecha_inicio_column_name = "Start"
        self.fecha_fin_column_name = "Finish"
        self.nivel_column_name = "Outline Level"


    def clean_files(self,purga_completa = True):
        """Limpia los archivos"""
        if self.proceso_completo:
            if self.local_filename is not None and  self.local_filename != "" and  os.path.exists(self.local_filename):
                logger.info(f"Eliminado:{self.local_filename}")
                os.remove(self.local_filename)
            logger.info(self.get_local_uid_path(self.uid))
            #Borrar data.json
            data_json = f'{self.get_local_uid_path(self.uid)}/data.json'
            if self.uid is not None and self.uid != "" and os.path.exists(data_json):
                logger.info(f"elimina:{data_json}")
                os.remove(data_json)

            #proceso para purgar completamente el directorio
            if purga_completa and self.uid is not None and self.uid != "" and self.proceso_completo:
                archivos = os.listdir(self.get_local_uid_path(self.uid))
                for archivo in archivos:
                    os.remove(f"{self.get_local_uid_path(self.uid)}/{archivo}")
                os.rmdir(self.get_local_uid_path(self.uid))

    def get_local_uid_path(self,uid = None):
        """Obtiene el path desde el uid"""
        if uid is not None and  uid != "":
            dir_procesa = 'procesa_archivos'
            if not os.path.exists(dir_procesa):
                os.mkdir(dir_procesa)
            dir_uid = f"{dir_procesa}/{uid}"
            if not os.path.exists(dir_uid):
                os.mkdir(dir_uid)
            return dir_uid
        else:
            return None

    def get_local_file_name(self,uid = None,filename = "archivo.xlsx"):
        """Obtiene el path del archivo local"""
        if uid is not None and  uid != "":
            dir_uid = self.get_local_uid_path(uid)
            return f"{dir_uid}/{filename}"
        else:
            return None

    def download_file(self,url, local_filename):
        """Descarga un archivo desde internet"""
        try:
            with requests.get(url, stream=True,timeout=30) as r:
                #r.raise_for_status()
                if r.status_code == 200:
                    with open(local_filename, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192): 
                            f.write(chunk)
                    self.local_filename = local_filename
                    return True
        except Exception as e:
            logger.error(str(e))
            return False
        return False

    def get_file(self,uid,filename):
        """descarga el archivo"""
        if self.continuar and os.path.exists(self.local_filename):
            return self.local_filename
        else:
            file_path = filename
            self.uid = uid
            if self.download:
                file_path= self.get_local_file_name(uid,"archivo.xlsx")
                
                if not self.download_file(filename,file_path):
                    self.error = True
                    self.message = "No se pudo descargar el archivo"
                logger.info(f"descarga {filename} {file_path}")
            else:
                file_path= self.get_local_file_name(uid,"archivo.xlsx")
                shutil.copy(filename,file_path)
            self.local_filename = file_path
            return self.local_filename

    def get_pandas(self,filename,download=False,uid = None):
        """Procesa obtiene un pandas dataframe de una url o un archivo local"""
        if download:
            self.download = True
        file_path = self.get_file(uid,filename)
        if self.error:
            return None
        else:
            logger.info(f"abriendo:{file_path}")
            df = pd.read_excel(file_path)
            logger.info(f"Retorna pandas:{file_path}")
            #logger.info(df)
            #logger.info(df.columns.values)
            if self.validar_archivo_excel(df):
                return df
            else:
                return None

    def list_columns(self,df:pd.DataFrame):
        """lista columnas del documento pandas/excel"""
        return df.columns.values

    def read_cell(self,df:pd.DataFrame,column_name,row_id):
        """Lee una celda especifica"""
        if row_id < 0 or row_id >= len(df):
            return None
        arr_cols = df.columns.values
        logger.info("cantidad columnas")
        logger.info(len(arr_cols))
        if len(arr_cols) > 0:
            #index_col = -1
            index_col = next((index for index, col in enumerate(arr_cols) if col == column_name), -1)
     
            #for index,col in enumerate(arr_cols):
            #    logger.debug(index)
            #    logger.debug(col)
            #    if col == column_name:
            #        index_col = index
            #logger.debug(row_id)
            #logger.debug(index_col)
            if index_col < 0:
                return None
            else:
                return df.iloc[row_id,index_col]
        else:
            return None

    def salvar_estado(self,error=False):
        """Salva el estado del proceso en un archivo json data.json"""
        data = {
            "board_id":self.board_id,
            "group_id":self.group_id,
            "item_id":self.item_id_l1,
            "pos":self.pos,
            "error":error,
            "message":str(self.message),
            "local_filename":str(self.local_filename),
            "sub_board_id":str(self.sub_board_id),
            "id_column_fecha_inicio":str(self.id_column_fecha_inicio),
            "id_column_fecha_fin":str(self.id_column_fecha_fin),
            "sub_board_id_column_fecha_inicio":str(self.sub_board_id_column_fecha_inicio),
            "sub_board_id_column_fecha_fin":str(self.sub_board_id_column_fecha_fin),
            "sub_board_columns_creadas":str(self.sub_board_columns_creadas),
        }
        text_json = json.dumps(data)
        logging.info(text_json)
        with open(f'{self.get_local_uid_path(self.uid)}/data.json', 'w') as outfile:
            json.dump(data, outfile)

    def listar_estado_texto(self):
        """Aplica un template jinja a la información de estado"""
        logger.info("obtiene informacion del proceso")
        template_env = Environment(loader=FileSystemLoader("templates"))
        template = template_env.get_template("response_template_estado_proceso_excel_uid.jinja")
        message = template.render(
            proceso = self
        )
        logger.info(message)
        return message

    def read_estado(self):
        """Recupera el estado del proceso del archivo json data.json"""
        path = f'{self.get_local_uid_path(self.uid)}/data.json'
        if os.path.exists(path):
            with open(path, 'r') as input:
                data = json.load(input)
            self.board_id = data["board_id"]
            self.group_id = data["group_id"]
            self.item_id_l1 = data["item_id"]
            if "sub_board_id" in data:
                self.sub_board_id = data["sub_board_id"]
            if "message" in data:
                self.message = data["message"]
            self.pos = data["pos"]
            if "error" in data:
                self.error = bool(data["error"])
            self.local_filename = data["local_filename"]
            if "id_column_fecha_inicio" in data:
                self.id_column_fecha_inicio = data["id_column_fecha_inicio"]
            if "id_column_fecha_fin" in data:
                self.id_column_fecha_fin = data["id_column_fecha_fin"]
            if "sub_board_id_column_fecha_inicio" in data:
                self.sub_board_id_column_fecha_inicio = data["sub_board_id_column_fecha_inicio"]
            if "sub_board_id_column_fecha_fin" in data:
                self.sub_board_id_column_fecha_fin = data["sub_board_id_column_fecha_fin"]
            if "sub_board_columns_creadas" in data:
                self.sub_board_columns_creadas = data["sub_board_columns_creadas"]
            logger.info("Fin de proceso")
            logger.info(self.board_id)
            logger.info(self.group_id)
            logger.info(self.item_id_l1)
            logger.info(self.pos)
            logger.info(self.error)
            logger.info(self.local_filename)
            return True
        return False

    def validar_archivo_excel(self,df):
        """Valida si el archivo excel posee todas las columnas requeridas"""
        required_columns = [
            self.titulo_column_name,
            self.fecha_inicio_column_name,
            self.fecha_fin_column_name,
            self.nivel_column_name
        ]

        if not all(col in df.columns for col in required_columns):
            self.error = True
            self.message = "Columnas requeridas no encontradas en el Excel"
            missing = [col for col in required_columns if col not in df.columns]
            self.message = f"Columnas requeridas faltantes: {', '.join(missing)}"
            return False
        else:
            return True


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
        if str(outline_lvl).strip() == '5':
            return 'subiteml2'#column
        if str(outline_lvl).strip() == '6':
            return 'subiteml3'#column
        if str(outline_lvl).strip() == '7':
            return 'subiteml4'#column
        return 'undefined'

    def parse_date(self,fecha:str):
        """parsea una fecha"""
        logger.info(fecha)
        logger.info(self.format_fecha_string)
        if fecha is not None:
            try:
                dt_fecha = datetime.strptime(f"{fecha}",self.format_fecha_string)
                time_delta = timedelta(hours=3)
                dt_fecha = dt_fecha + time_delta
                resp_fecha = str(dt_fecha)
                logger.info(resp_fecha)
                return resp_fecha
            except Exception as e:
                logger.error(str(e))
                logger.info(f"no se pudo parsear la fecha {fecha}")
                return None
        else:
            return None
  
    def process_excel_monday(self,filename, download:bool , monday_client:MondayClient,uid = None,rows=0,continuar:bool = False):
        """Procesa el excel de monday si se le da una url asignar el parametro download = True, si se desea procesar una cantidad limitada de filas asignar un valor a rows si el valor es 0 procesara todo el documento"""
        self.error = False
        self.message = ""
        self.continuar = continuar
        #Actualmente sobrescribe el archivo si continua
        logger.info(download)
        df = self.get_pandas(filename,download,uid)
        if self.error or df is None:
            self.salvar_estado(self.error)
        else:
            logger.info(self.list_columns(df))
            logger.info(uid)
            cant_total_filas = len(df.index)
            cantidad_a_procesar = 0
            self.procesando = True
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
                        title = self.read_cell(df,self.titulo_column_name,i)
                        dt_inicio = self.read_cell(df,self.fecha_inicio_column_name,i)
                        dt_fin = self.read_cell(df,self.fecha_fin_column_name,i)
                        fecha_inicio = self.parse_date(dt_inicio)
                        fecha_fin = self.parse_date(dt_fin)
                        outline_lvl = self.read_cell(df,self.nivel_column_name,i)
                        message = f"Row: {i}"
                        logger.info(message)
                        logger.info(title)
                        logger.info(outline_lvl)
                        logger.info(self.identify_type(outline_lvl))
                        if self.identify_type(outline_lvl) == 'board':
                            self.board_id = self.xls_create_board(monday_client,title,'public')
                            self.id_column_fecha_inicio = self.xls_create_column(monday_client,self.board_id,"Inicio","Fecha inicio","date")
                            self.id_column_fecha_fin = self.xls_create_column(monday_client,self.board_id,"Fin","Fecha fin","date")
                            self.id_column_crono = self.xls_create_column(monday_client,self.board_id,"Crono","Crono","timeline")
                            self.id_column_persona = self.xls_create_column(monday_client,self.board_id,"Responsable Monday","responsable","text")
                            self.id_column_responsable = self.xls_create_column(monday_client,self.board_id,"Responsable Externo","responsable","text")
                        if self.identify_type(outline_lvl) == 'group':
                            self.group_id = self.xls_create_group(monday_client,title,self.board_id)
                        if self.identify_type(outline_lvl) == 'item':
                            self.item_id_l1 = self.xls_create_item(monday_client,title,self.board_id,self.group_id)
                            #self.xls_asign_value_to_column(monday_client,self.board_id,self.item_id_l1,self.id_column_fecha_inicio,fecha_inicio)
                            #self.xls_asign_value_to_column(monday_client,self.board_id,self.item_id_l1,self.id_column_fecha_fin,fecha_fin)
                            self.xls_asign_values_columns_primary_board(monday_client,self.board_id,self.item_id_l1,fecha_inicio,fecha_fin,None,"pepe")
                        if self.identify_type(outline_lvl) == 'subiteml1':
                            self.item_id_l2 = self.xls_create_sub_item(monday_client,title,self.item_id_l1,fecha_inicio)
                            if not self.sub_board_columns_creadas:
                                self.sub_board_id = self.get_sub_board_id_sub_item(monday_client,self.item_id_l1)
                                self.sub_board_id_column_fecha_inicio = self.xls_create_column(monday_client,self.sub_board_id,"Inicio","Fecha inicio","date")
                                self.sub_board_id_column_fecha_fin = self.xls_create_column(monday_client,self.sub_board_id,"Fin","Fecha fin","date")
                                self.sub_board_id_column_crono = self.xls_create_column(monday_client,self.sub_board_id,"Crono","Crono","timeline")
                                self.sub_board_id_column_persona = self.xls_create_column(monday_client,self.sub_board_id,"Responsable Monday","responsable","text")
                                self.sub_board_id_column_responsable = self.xls_create_column(monday_client,self.sub_board_id,"Responsable Externo","responsable","text")
                                self.sub_board_columns_creadas = True
                            self.get_sub_board_id_sub_item(monday_client,self.item_id_l1)
                            #self.xls_asign_value_to_column(monday_client,self.sub_board_id,self.item_id_l2,self.sub_board_id_column_fecha_inicio,fecha_inicio)
                            #self.xls_asign_value_to_column(monday_client,self.sub_board_id,self.item_id_l2,self.sub_board_id_column_fecha_fin,fecha_fin)
                            self.xls_asign_values_columns_sub_board(monday_client,self.sub_board_id,self.item_id_l2,fecha_inicio,fecha_fin,None,"pepe")

                        if self.identify_type(outline_lvl) == 'subiteml2' and self.cargar_lvl_superirores_a_como_subitems:
                            self.item_id_l3 = self.xls_create_sub_item(monday_client,title,self.item_id_l1,fecha_inicio)
                        if self.identify_type(outline_lvl) == 'subiteml3' and self.cargar_lvl_superirores_a_como_subitems:
                            self.item_id_l4 = self.xls_create_sub_item(monday_client,title,self.item_id_l1,fecha_inicio)
                        if self.identify_type(outline_lvl) == 'subiteml4' and self.cargar_lvl_superirores_a_como_subitems:
                            self.item_id_l5 = self.xls_create_sub_item(monday_client,title,self.item_id_l1,fecha_inicio)
                        if self.esperar:
                            time.sleep(self.wait_time)  # Pauses execution for 3 seconds.
                        if self.detener:
                            break
                if self.sub_board_id is not None:
                    self.xls_delete_column(monday_client,self.sub_board_id,"person")
                    self.xls_delete_column(monday_client,self.sub_board_id,"status")
                    self.xls_delete_column(monday_client,self.sub_board_id,"date0")
            except Exception as e:
                self.error = True
                self.message = str(e)
                logger.error(str(e))
                self.procesando = False
            logger.info("Fin de proceso")
            logger.info(self.board_id)
            logger.info(self.group_id)
            logger.info(self.item_id_l1)
            logger.info(self.pos)
            if cant_total_filas == self.pos:
                #Si llego al ultimo registro marco el proceso como completado
                #El objetivo del flag de proceso completo es identificar si el proceso llego a procesar hasta la ultima linea del archivo
                self.proceso_completo = True
            
            self.salvar_estado(self.error)
            self.clean_files()
            self.procesando = False

    def limpiar_nombre(self,texto:str):
        """Limpia el texto de un titulo"""
        texto_con_escapeo = str(texto).replace("\\","\\\\")
        texto_con_escapeo = str(texto_con_escapeo).replace("\"","\\\"")
        return texto_con_escapeo

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
    
    def xls_delete_column(self,monday_client:MondayClient,board_id:str,column_id):
        """Elimina una columna de monday.com"""
        mutation = """
        mutation {
            delete_column (board_id: %s, column_id: "%s") {
                id
            }
        }
        """ % (board_id,column_id)
        logger.info(mutation)
        response = monday_client.custom._query(mutation)
        logger.info(response)
        id_col = response["data"]["delete_column"]["id"]
        logger.info(id_col)
        return id_col

    def xls_create_column(self,monday_client:MondayClient,board_id:str,title:str,description:str,column_type:str):
        """Crea una columna en un board"""
        # Construir mutación GraphQL
        mutation = """
            mutation {
                create_column (
                    board_id: %s,
                    title: "%s",
                    description:"%s",
                    column_type: %s
                ) {
                    id
                }
            }
        """ % (board_id,title,description,column_type)
        logger.info(mutation)
        response = monday_client.custom._query(mutation)
        logger.info(response)
        id_col = response["data"]["create_column"]["id"]
        logger.info(id_col)
        return id_col

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
        respuesta = monday_client.items.create_item( item_name= self.limpiar_nombre(item_name) ,board_id=board_id ,group_id=group_id)
        #item_name_limpio = self.limpiar_nombre(item_name)
        #mutation = """mutation {
        #create_item(
        #    board_id: %s, 
        #    group_id: "%s", 
        #    item_name: "%s", 
        #    column_values: %s
        #    ) {
        #    id
        #}
        #}""" % (board_id,group_id, item_name_limpio ,column_values)
        #logger.info(mutation)
        #respuesta = monday_client.custom._query(mutation)
        logger.info(respuesta)
        item_id = respuesta['data']['create_item']['id']
        logger.info(item_id)
        return item_id
    
    def xls_asign_value_to_column(self,monday_client:MondayClient,board_id:str,item_id:str,column_id:str,column_value:str):
        """Asigna un valor a una columna"""
        mutation = """
        mutation {
            change_simple_column_value (board_id: %s, item_id: %s, column_id: "%s", value: "%s") {
                id
            }
        }
        """ % (board_id,item_id,column_id,column_value)
        logger.info(mutation)
        response = monday_client.custom._query(mutation)
        logger.info(response)
    
    def xls_asign_value_to_column_multiple(self,monday_client:MondayClient,board_id:str,item_id:str,column_value:str):
        """Asigna un valor a una columna"""
        mutation = """
        mutation {
            change_multiple_column_values (board_id: %s, item_id: %s, column_values: %s) {
                id
            }
        }
        """ % (board_id,item_id,column_value)
        logger.info(mutation)
        response = monday_client.custom._query(mutation)
        logger.info(response)

    def xls_asign_values_columns_primary_board(self,monday_client:MondayClient,board_id:str,item_id:str,fecha_inicio:str,fecha_fin:str,persona:str,responsable:str):
        """Asigna todas las columnas del board principal"""
        #"{\"timeline\":{\"from\":\"2025-10-14\",\"to\":\"2025-10-21\"}}"
        value_dict = {self.id_column_crono:{
                            "from":fecha_inicio,
                            "to":fecha_fin},
                        self.id_column_fecha_inicio : fecha_inicio ,
                        self.id_column_fecha_fin : fecha_fin ,
                        self.id_column_persona : persona ,# ver como asignar
                        self.id_column_responsable : responsable
                      }
        #value_dict = {column_id:{"from":"2025-10-14","to":"2025-10-21"}}
        value = json.dumps(json.dumps(value_dict))
        return self.xls_asign_value_to_column_multiple(monday_client,board_id,item_id,value)
    
    def xls_asign_values_columns_sub_board(self,monday_client:MondayClient,board_id:str,item_id:str,fecha_inicio:str,fecha_fin:str,persona:str,responsable:str):
        """Asigna todas las columnas del board secundario"""
        #"{\"timeline\":{\"from\":\"2025-10-14\",\"to\":\"2025-10-21\"}}"
        value_dict = {self.sub_board_id_column_crono:{
                            "from":fecha_inicio,
                            "to":fecha_fin},
                        self.sub_board_id_column_fecha_inicio : fecha_inicio ,
                        self.sub_board_id_column_fecha_fin : fecha_fin ,
                        self.sub_board_id_column_persona : persona ,# ver como asignar
                        self.sub_board_id_column_responsable : responsable
                      }
        value = json.dumps(json.dumps(value_dict))
        return self.xls_asign_value_to_column_multiple(monday_client,board_id,item_id,value)

    def get_sub_board_id_sub_item(self,monday_client:MondayClient,item_id:str):
        """Asigna un valor a una columna"""
        mutation = """
        query {
            items (ids: %s) {
                subitems {
                id
                board{
                    id
                }
                column_values {
                    value
                    text
                }
                }
            }
        }
        """ % (item_id)
        logger.info(mutation)
        response = monday_client.custom._query(mutation)
        logger.info(response)
        sub_board_id = ""
        for item in response["data"]["items"]:
            for subitem in item["subitems"]:
                sub_board_id = subitem["board"]["id"]
                logger.info(sub_board_id)
        return sub_board_id

    def xls_create_sub_item(self,monday_client:MondayClient,item_name,item_id,fecha_inicio:str):
        """Crea un subitem"""
        text = f"Create sub item: {item_name} {item_id}"
        logger.info(text)
        subitem_name_limpio = self.limpiar_nombre(item_name)
        respuesta = monday_client.items.create_subitem(subitem_name = subitem_name_limpio,parent_item_id = item_id)
        logger.info(respuesta)
        item_id = respuesta['data']['create_subitem']['id']
        logger.info(item_id)
        return  item_id
    
    def analizar_excel(self,filename, download ,uid = None):
        """Analiza los niveles de profundidad del archivo excel"""
        arr_analisis_items = []
        if os.path.exists(filename):
            df = self.get_pandas(filename,download,uid)
            if df is not None:
                cant_total_filas = len(df.index)
                analisis_item = AnalisisItem()
                primer_item = True
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
        return arr_analisis_items

class Hilo():
    hilo:Thread
    proceso_excel:ExcelUtilsMonday

    def __init__(self):
        pass