"""
    Post hooks
"""
from cvs_services.config import Connections, Response  
from bottle import response  

def close_connection():
    try:
        mysqldb = Connections()['mysqldbconnection']
        mysqldb.close()
    except:
        pass
    
def add_headers():    
    try:
        response.set_header('count', Response()['Count']) 
    except:
        pass