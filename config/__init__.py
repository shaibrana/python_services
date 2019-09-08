class Connections(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = {'mysqldbconnection':args[0]}
        return cls._instance

class Headers(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = args[0]
        return cls._instance
    
class Response(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = args[0]
        return cls._instance
    


