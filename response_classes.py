
class ResponseItems:
    cursor:str
    items = []

    def __init__(self):
        pass

class ResponseBoard:
    name:str
    items_page = [ResponseItems]

    def __init__(self,name:str):
        self.name = name

class ResponseExtensions:
    request_id:str

class ResponseData:
    boards = [ResponseBoard]
    extensions: ResponseExtensions
    account_id:str

    def __init__(self):
        pass
