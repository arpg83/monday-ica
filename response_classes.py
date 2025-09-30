import json

class Column:
    id:str
    text:str
    type:str
    status:str
    value:str

class Item:
    id:str
    name:str
    columns:Column = []

    def __init__(self):
        self.id = ""
        self.name = ""
        self.columns = []

class Group:
    id:str
    title:str
    items:Item = []

    def __init__(self):
        self.id = ""
        self.title = ""
        self.items = []

class Board:
    name:str
    id:str
    groups:Group = []

    def __init__(self):
        self.name = ""
        self.groups = []

    def find_group_by_id(self,id:str,create= False):
        for grupo in self.groups:
            if grupo.get_id() == id:
                return grupo
        if create:
            grupo = Group()
            grupo.id = id
            self.groups.append(grupo)
            return grupo
        return None
    
    def find_group_by_str(self,text:str,create= False):
        obj_value = eval(text)
        for grupo in self.groups:
            if grupo.id == obj_value['id']:
                return grupo
        if create:
            grupo = Group()
            grupo.id = obj_value['id']
            grupo.title = obj_value['title']
            print("Agregando objeto")
            self.groups.append(grupo)
            return grupo
        return None
