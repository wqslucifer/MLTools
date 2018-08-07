

def init():
    global global_dict
    global_dict = dict()

def set_value(key, value):
    global_dict[key] = value


def get_value(key, defValue=None):
    try:
        return global_dict[key]
    except KeyError:
        return defValue
