from subitem_response import SubItem
""" Clase para usar en template de item list"""
class ItemResponse:
    """Clase para listar de Item de monday"""
    id:str
    name:str
    subitems:list[SubItem]

    def __init__(self):
        pass

