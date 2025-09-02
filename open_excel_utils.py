
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
    logger.info(df)
    logger.info(df.columns.values)
    return df


