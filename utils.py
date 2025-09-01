def dict_read_property(item,id_prop):
    for id_prop_act in item:
        if id_prop_act == id_prop:
            return item[id_prop_act]
    return None

def dict_read_property_into_array(item,id_prop):
    #print(item)
    for arr_item in item:
        #print(arr_item)
        for id_prop_act in arr_item:
            if id_prop_act == id_prop:
                return arr_item[id_prop_act]
    return None

def dict_get_array(item):
    array = []
    for arr_item in item:
        array.append(arr_item)
    return array

def dict_list_prop_id(item):
    array = []
    #for arr_item in item:
        #print(arr_item)
    if not item == None:
        for id_prop_act in item:
            array.append(id_prop_act)
    return array