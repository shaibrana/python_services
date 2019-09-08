
import json
import hashlib
import cvs_services.hooks.pre as pre_hook
import cvs_services.hooks.post as post_hook
from bottle import route, run, hook, response, request, HTTPResponse, default_app, post


from cvs_services.components.users       import controller as user
from cvs_services.components.orders      import controller as order

from cvs_services.config import Headers
import cvs_services.dal as dbm


user_obj         = user.ControllerUserClass()
order_obj       = order.ControllerOrderClass()

db = dbm.DBLayer()

@route('/hello')
def hello():
    print "hello"  
    response={}
    response['status']  = "success"
    response['message'] = "Hello to VT Services."
    return response

# --------------------------------------------------- Users Services ------------------------------------------------------------------- #
        
@route('/users/register', method='POST')
def user_register():
    """ 
    This service is use to register user with email. 
    The key parameters that must have to send in post data are :
    postParameters = ['first_name','last_name','email','phone']
    In case of user registration response will be status: success and a message will be return like user registration successfully.
    If user's email is already exist in our system then response will be status: failure and message will be already registered with this email.
    In case of any error during server process or query error has occurred response will be status: failure and message will be like Exception Error.
    """
    
    data = user_obj.user_register(request.forms)              
    return data

@route('/users/forgot/password', method='POST')
def user_forgotpassword():
    """
    This is to forgot password.
    """  
    data = user_obj.user_forgotpassword(request.forms)              
    return data

@route('/users/login')
def user_login():
    """ This is to user login. """
    
    data = user_obj.user_login()
    return data



@route('/users/update/profile', method='POST')
def user_update_profile():
    
    """ This is to update user profile data."""
    
    if 'userid' and 'email' not in request.forms:
        return {'status':'Failure','message':'User Id is missing,please try with correct data.'}
    
    data = user_obj.user_update_profile(request.forms)
    return data
   
@route('/users/info')
def get_users_info():
    """
    This is to get info of single user (new)
    """ 
    
    data = user_obj.get_users_info()
    return data

#**************** Customer **************************#
@route('/customers/all')
def get_all_customers():
    """ This is to get all customers data related to business owner and system admin. """
    data = user_obj.get_all_customers()
    return data

@route('/customers/count')
def get_all_customers_count():
    """ This is to get all customers data related to business owner and system admin.. """
    data = user_obj.get_all_customers("1")
    return data

@route('/customer/orders/customerId/:customerId')
def get_customer_orders(customerId):
    """ This is to get all customers data related to business owner and system admin. """
    data = user_obj.get_customer_orders(customerId)
    return data

@route('/customer/orders/count/customerId/:customerId')
def get_customer_orders_count(customerId):
    """ This is to get all customers data related to business owner and system admin. """
    data = user_obj.get_customer_orders(customerId,"1")
    return data

@route('/customer/update',method='POST')
def update_customer_status():
    """ This is to get all customers data related to business owner and system admin."""
    data = user_obj.update_customer_status(request.forms)
    return data

@route('/sms/log',method='POST')
def sms_log():
    """ This is to save sms log."""
    data = user_obj.sms_log(request.forms)
    return data




#*******************************************ORDERS***********************************************************************************************************************************#
# @route('/orders/all')
# def get_all_orders():
#     """
#     This is to get info of all orders
#     """ 
#     
#     data = order_obj.get_all_orders()
#     return data
# 
# @route('/orders/detail/orderid/:orderid')
# def get_one_order(orderid):
#     """This service use to get one order detail.""" 
#     data = order_obj.get_all_orders(orderid)
#     return data

@route('/orders/all')
def get_all_orders():
    """
    This is to get info of all orders
    """ 
    data = order_obj.get_all_orders()
    return data

@route('/orders/count')
def get_all_orders_count():
    """
    This is to get info of all orders
    """ 
    data = order_obj.get_all_orders("1")
    return data


@route('/orders/detail/orderid/:orderid')
def get_order_detail(orderid):
    """This service use to get one order detail.""" 
    data = order_obj.get_order_detail(orderid)
    return data

@route('/orders/detail/count/orderid/:orderid')
def get_order_detail_count(orderid):
    """This service use to get one order detail.""" 
    data = order_obj.get_order_detail(orderid,"1")
    return data


@route('/orders/update/status', method='POST')
def order_update_status():
        
    """ This service is use to update order status. """
    result = order_obj.order_update_status(request.forms) 
    return result

@route('/orders/update/print', method='POST')
def order_update_print():
        
    """ This service is use to update order status. """
    result = order_obj.order_update_print(request.forms) 
    return result


@route('/products/all')
def get_all_products():
    
    """ This service is use to get products list. """
    data = order_obj.get_all_products()
    return data

@route('/orders/add/product', method='POST')
def add_products():
        
    """ This service is use to update order status. """
    result = order_obj.add_products(request.forms) 
    return result

# @route('/orders/remove/orderId/:orderid' , method='POST')
# def remove_order(orderid):
#     """This service use to remove one item from order detail.""" 
#     data = order_obj.remove_order(orderid)
#     return data


# @route('/orders/item/remove/orderid/:orderid/detailid/:detailid' , method='POST')
# def remove_item_from_order(orderid,detailid):
#     """This service use to remove one item from order detail.""" 
#     data = order_obj.remove_item_from_order(orderid,detailid)
#     return data
# 
# 
# @route('/orders/items/remove' , method='POST')
# def remove_items_from_order():
#     """This service use to remove multiple item from order detail.""" 
#     data = order_obj.remove_items_from_order(request.forms)
#     return data

@route('/orders/item/remove/orderid/:orderid/detailid/:detailid' , method='POST')
def remove_item_from_order(orderid,detailid):
    """This service use to remove one item from order detail.""" 
    data = order_obj.remove_item_from_order(orderid,detailid)
    return data


@route('/orders/items/remove' , method='POST')
def remove_items_from_order():
    """This service use to remove multiple item from order detail.""" 
    data = order_obj.remove_item_from_order(None,None,request.forms)
    return data


@route('/orders/item/change/detailid/:detailid/newQuantity/:newQuantity' , method='POST')
def change_item_quantity_from_order(detailid,newQuantity):
    """This service use to change one quantity item order detail.""" 
    data = order_obj.change_item_quantity_from_order(detailid,newQuantity)
    return data

@route('/orders/messages/orderid/:orderid')
def get_messages_log(orderid):
    """This service use to get one order messages log.""" 
    data = order_obj.get_messages_log(orderid)
    return data

@route('/orders/message/send' , method='POST')
def send_owner_message():
    """This service use to send owner sms to customers.""" 
    data = order_obj.send_owner_message(request.forms)
    return data


# ********************************************************************************************************************************************************************************** #
@hook('before_request')
def pre_request():
    pre_hook.initialize()
    pre_hook.get_headers(request.headers)
    pre_hook.authenticate()
    pre_hook.establish_connection()
    
    
@hook('after_request')
def post_request():
    post_hook.close_connection()
    post_hook.add_headers()

