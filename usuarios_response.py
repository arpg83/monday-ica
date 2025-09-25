""" Clase para usar en template de users"""
class Usuario:
    """Clase para listar usuarios de monday"""
    id:str
    name:str
    email:str
    enabled:str
    teams = []

    def __init__(self):
        pass

