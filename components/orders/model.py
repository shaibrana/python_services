import cvs_services.dal as dbm
import base64
import binascii
import random
import string
import time
import datetime
import calendar as cal
import dateutil.relativedelta
import hashlib
import smtplib
import urllib2
import json
import re
import phonenumbers 

import urllib
import requests
from requests.auth import HTTPBasicAuth

import twilio
import twilio.rest
from twilio.rest import TwilioRestClient
    
#import sys;
#reload(sys);
#sys.setdefaultencoding("utf8")

#import requests
#from StringIO import StringIO


from cvs_services.config import Headers
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
db = dbm.DBLayer()

class ModelOrderClass:
    global AccountID
    AccountID = 'act_300362'
    global LocationID 
    LocationID = 'loc_185100'
    global APIKey 
    APIKey = '98f6b43c86f4fa073efac31f8c37dc6d'
    global SecureTransactionKey 
    SecureTransactionKey = '99d3fa5818f668b8f6172d031316646d'  
    global auth_token
    auth_token =  "Basic "+base64.b64encode(APIKey+':'+SecureTransactionKey)
    global url
    url = 'https://sandbox.forte.net/api/v2/';  
    
    """ Twilio """
    global twilio_account_sid
    twilio_account_sid = "ACb96b79198137f79f0fd78cc195bc42d0"
    global twilio_auth_token
    twilio_auth_token  = "9e1b9f25c3aa12130a5e75ecda5b503e"
    global twilio_client
    twilio_client = twilio.rest.TwilioRestClient(twilio_account_sid, twilio_auth_token)
    global twilio_number
    twilio_number = "+16193910014"
    
    def get_all_orders(self,ordersCount=None):
        response  = {}

        try:

            athentication = base64.b64decode(Headers()['Authentication'])
            i = athentication.split(':')
            username = i[0]
            password = i[1]
                
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            count = db.get_count('users',where,countValues)
               
            if count ==0:    
                response['status']  = "Failure"
                response['message'] = "Please try with valid user name and password."
                return response
            
            order_id=""
            order_status=""
            
            what="userid,user_type"
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            user_detail=db.get_all('users',what,where,countValues)
        
           
            owner_id=user_detail[0]['userId']
            user_type=user_detail[0]['userType']
            
        
            countValues = {}
            
            what = "orders.order_id,orders.user_number,orders.owner_number,orders.owner_id,orders.is_print,DATE_FORMAT(orders.date_begin,'%%Y-%%m-%%d %%H:%%i:%%s') as date_created,orders.status,DATE_FORMAT(orders.date_updated,'%%Y-%%m-%%d %%H:%%i:%%s') as date_updated,orders.delivery_address,customers.first_name,customers.last_name"
            where = "WHERE orders.user_number=customers.mobile_number AND orders.status!='pending'"
            table = "orders,customers"
               
            if  user_type == "sys_admin":
                where +=" and orders.owner_id = users.userid";
                what += ",users.business_name"
                table += ",users"
            else:
                where +=  " AND orders.owner_id = %(owner_id)s AND orders.status!='system_error'" 
                countValues.update({'owner_id': (owner_id)})
            
               
             
            orderid = Headers()['id']
            if orderid:
                where += " AND orders.order_id = %(order_id)s"
                countValues.update({'order_id':(orderid)})
            
            searchKeyWord=Headers()['searchKeyWord']
            if searchKeyWord:
                where += " AND (orders.user_number LIKE %(user_number)s OR customers.first_name LIKE %(first_name)s OR customers.last_name LIKE %(last_name)s"
                
                if user_type == "sys_admin":
                    where += " OR users.business_name LIKE %(business_name)s OR users.owner_uniquecode LIKE %(owner_uniquecode)s"
                    countValues.update({'business_name':'%'+(searchKeyWord)+'%','owner_uniquecode':'%'+(searchKeyWord)+'%'})
                
                where += ")"
                countValues.update({'user_number':'%'+(searchKeyWord)+'%','first_name':'%'+(searchKeyWord)+'%','last_name':'%'+(searchKeyWord)+'%'})
                
            status = Headers()['status']
            if status:
                if status == "archive":
                    where += " AND orders.is_archive = 1"
                else:    
                    where += " AND orders.status = %(status)s"
                    countValues.update({'status':(status)})
            else:
                if user_type != "sys_admin":
                    where += " AND orders.is_archive = 0"
                
            
            if ordersCount == None:
            
                where += " ORDER BY orders.order_id desc"
                
                
                offset = Headers()['vtOffset']
                limit = Headers()['vtLimit']
                
                if offset != "" and limit != "":
                    offset_limit = (int(offset) - 1)*int(limit) 
                    where += " LIMIT "+limit+" OFFSET "+str(offset_limit)+" "
                
                elif limit != "":
                    where += " LIMIT "+limit
                
                else:
                    print "send limit with offset"
            
            if ordersCount != None:
                result = db.get_all(table,"orders.order_id",where,countValues)
                response['status']  = "Success"
                response['data'] = len(result)
                return response
            
            else:
                result = db.get_all(table,what,where,countValues)
                
                for single in result: 
                    
                    obj = single
                    orderId = obj['orderId']
                    what="count(order_detail_id) as totalProducts, sum(quantity) as totalQuantity"
                    where = "WHERE order_id = %(orderId)s"
                    countValues = {'orderId': (orderId)}
                    order_detail=db.get_all('order_details',what,where,countValues)
                    if order_detail[0]['totalProducts']:
                        totalProducts = order_detail[0]['totalProducts']
                        totalQuantity = order_detail[0]['totalQuantity']
                        obj["totalProducts"] = totalProducts
                        obj["totalQuantity"] = str(totalQuantity)
                        orderDetail = self.get_order_detail(orderId)
                        
                        obj["taxAmount"] = orderDetail['data'][0]['taxAmount']
                        obj["deliveryCharge"] = orderDetail['data'][0]['deliveryCharge']
                        obj["totalAmount"] = orderDetail['data'][0]['totalAmount']
                        obj["convenienceChargeCustomer"] = orderDetail['data'][0]['convenienceChargeCustomer']
                        obj["itemsAmount"] = orderDetail['data'][0]['itemsAmount']
                        obj["orderDetail"] = orderDetail['data'][0]['orderDetail']
                     
                
                response['status']  = "Success"
                response['data'] = result
                return response
            
        
        except:
            response['status']  = "Failure"
            response['message'] = "Exception Error."
            return response
        
    
    
    def get_order_detail(self,orderId,ordersCount=None):
            
        response = {}                     
        try:

            athentication = base64.b64decode(Headers()['Authentication'])
            i = athentication.split(':')
            username = i[0]
            password = i[1]
               
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            count = db.get_count('users',where,countValues)
              
            if count ==0:    
                response['status']  = "Failure"
                response['message'] = "Please try with valid user name and password."
                return response
            
            what="userid,user_type"
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            user_detail=db.get_all('users',what,where,countValues)
       
          
            owner_id=user_detail[0]['userId']
            user_type=user_detail[0]['userType']
           
            order_id = int(orderId)
               
            what = "order_id,user_number,owner_number,owner_id,status,is_payment,delivery_address,total_amount,is_archive,is_print,DATE_FORMAT(orders.date_begin,'%%Y-%%m-%%d %%H:%%i:%%s') as date_created,DATE_FORMAT(orders.date_updated,'%%Y-%%m-%%d %%H:%%i:%%s') as date_updated"
            where= "where order_id = %(order_id)s"
            allValues = {'order_id':(order_id)}
               
            if user_type == "business_owner":
                where += " AND owner_id = %(owner_id)s"
                allValues.update({'owner_id':(owner_id)})
               
            result = db.get_all('orders',what,where,allValues)
           
            if not result:
                response['status']  = "Failure"
                response['message'] = "Please try with valid orderId."
                return response
            
            if ordersCount != None:
                what = "order_detail_id"
                where= "where order_details.product_id=products.product_id AND order_id = %(order_id)s"
                allValues = {'order_id':(order_id)}
                order_details= db.get_all('order_details,products',what,where,allValues)
                
                response['status']  = "Success"
                response['data'] = len(order_details)
                return response
            
            else:
                what = "order_detail_id,order_details.product_id,base_price,quantity,products.product_name"
                where= "where order_details.product_id=products.product_id AND order_id = %(order_id)s"
                allValues = {'order_id':(order_id)}
                   
                order_details= db.get_all('order_details,products',what,where,allValues)
                result[0]['orderDetail'] = order_details
                
                what = "sum(base_price * quantity) as total_amount"
                where= "where order_id = %(order_id)s"
                allValues = {'order_id':(order_id)}
                total_amount_detail = db.get_all('order_details',what,where,allValues)
              
                if total_amount_detail[0]['totalAmount'] != None:
                   
                    amount = total_amount_detail[0]['totalAmount']
                    result[0]['itemsAmount'] = format(amount, '.2f')
                    owner_id = result[0]['ownerId']
                    what="tax_rate,delivery_charge,convenience_charge_customer"
                    where = "WHERE userid = %(owner_id)s"
                    countValues = {'owner_id': (owner_id)}
            
                    user_detail=db.get_all('user_rules',what,where,countValues)
                    tax_rate=user_detail[0]['taxRate']
                    deliveryCharge = user_detail[0]['deliveryCharge']
                    convenienceChargeCustomer=user_detail[0]['convenienceChargeCustomer']
                   
                   
                    order_amount_with_tax = self.get_amount(order_id,owner_id)
                    tax_rate = order_amount_with_tax -  amount - float(convenienceChargeCustomer)-float(deliveryCharge)
                    
                    result[0]['deliveryCharge'] = format(float(deliveryCharge), '.2f')
                    result[0]['convenienceChargeCustomer'] = format(float(convenienceChargeCustomer), '.2f')
                    result[0]['taxAmount'] = format(tax_rate, '.2f')
                    result[0]['totalAmount'] = format(order_amount_with_tax, '.2f')
                    
                    response['status']  = "Success"
                    response['data'] = result
                    return response
                
                response['status']  = "Failure"
                response['message'] = "No product detail"
                return response
       
        except:
            response['status']  = "Failure"
            response['message'] = "Exception Error."
            return response

    def check_valid_status(self,orderId,status):
        response = {}
        
        what="settlement_id,status"
        where = "WHERE order_id = %(orderId)s"
        countValues = {'orderId': (orderId)}
        
        order_detail=db.get_all('orders',what,where,countValues)
        current_order_status=order_detail[0]['status']
        settlement_id=order_detail[0]['settlementId']
        
        if current_order_status == "open":
            if status=="closed":
                 response['status']  = "Success"
                 response['message'] = ""
                 return response
            elif status=="cancel":
                 response['status']  = "Success"
                 response['message'] = ""
                 return response
            else:
                 response['status']  = "Failure"
                 response['message'] = "Sorry try again with valid Status. valid status are closed,cancel"
                 return response
       
        
        elif current_order_status == "closed":
            
            if status=="open":
                 if settlement_id != None:
                     response['status']  = "Failure"
                     response['message'] = "Sorry can not change status. Because settlement is made for this order"
                     return response
                 else:
                     response['status']  = "Success"
                     response['message'] = ""
                     return response
           
            elif status=="cancel":
                 if settlement_id != None:
                     response['status']  = "Failure"
                     response['message'] = "Sorry can not change status. Because settlement is made for this order"
                     return response
                 else:
                     response['status']  = "Success"
                     response['message'] = ""
                     return response
            
            elif status=="archive":
                 response['status']  = "Success"
                 response['message'] = ""
                 return response
            
            else:
                 response['status']  = "Failure"
                 response['message'] = "Sorry try again with valid Status. valid status are open,cancel,archive"
                 return response
        else:
             response['status']  = "Failure"
             response['message'] = "Sorry try again with valid Status"
             return response
        
    def save_transaction_detail(self,response,status,orderId):
    
        now  = datetime.datetime.now()
        date = now.strftime("%Y-%m-%d")
        currentdate = now.strftime("%Y-%m-%d %H:%M:%S")
        json_response = json.dumps(response)
        column = ['transaction_response','status','orderid','date_created']
        value = [json_response,status,orderId,currentdate]
        result = db.insert_query('transactions',column,value)
        return "Success"    
                 
    
    def change_status(self,orderId,status):
    
        now  = datetime.datetime.now()
        date = now.strftime("%Y-%m-%d")
        currentdate = now.strftime("%Y-%m-%d %H:%M:%S")
        where = "WHERE order_id = %(orderId)s"
        updateValues = {'orderId':(orderId),'date_updated':(currentdate)}
        new_values = "date_updated = %(date_updated)s"
             
        if status == "archive":
            new_values += ",is_archive = '1'"
        else:
            new_values += ",status = %(status)s"
            updateValues.update({'status':(status)})
            
        db.update_query('orders', new_values,where,updateValues)
        return "Success"    
    
    def custom_message(self,system_name):
        what="*"
        where = "WHERE system_name = %(system_name)s"
        countValues = {'system_name': (system_name)}
        result=db.get_all('custom_default_messages',what,where,countValues)
        return result
    
    
    def replace_variables(self,message,owner_id,order_id=None):
        
        what="business_name,mob_number"
        where = "WHERE userid = %(owner_id)s"
        countValues = {'owner_id': (owner_id)}
        owner_detail=db.get_all('users',what,where,countValues)
        businessName=owner_detail[0]['businessName'];
        mob_number=owner_detail[0]['MobileNumber'];
        clean_phone_number = re.sub('[^0-9]+', '', mob_number)
        formatted_phone_number = re.sub("(\d)(?=(\d{3})+(?!\d))", r"\1-", "%d" % int(clean_phone_number[:-1])) + clean_phone_number[-1]
        
        
        what="delivery_time,pickup_time"
        where = "WHERE userid = %(owner_id)s"
        countValues = {'owner_id': (owner_id)}
        owner_detail=db.get_all('user_rules',what,where,countValues)
        deliveryTime=owner_detail[0]['deliveryTime'];
        pickupTime=owner_detail[0]['pickupTime'];
        if order_id!=None:
            what="total_amount,delivery_address"
            where = "WHERE order_id = %(order_id)s"
            countValues = {'order_id': (order_id)}
            owner_detail=db.get_all('orders',what,where,countValues)
            deliveryAddress=owner_detail[0]['deliveryAddress'];
            totalAmount=owner_detail[0]['totalAmount'];
            try:
                message = message.replace("%order_amount%",totalAmount)
            except:
                print ""
            
            try:
                message = message.replace("%pickup_time%",pickupTime)
            except:
                print ""
            
            try:
                message = message.replace("%order_id%",order_id)
            except:
                print ""
            
            try:
                message = message.replace("%delivery_address%",deliveryAddress)
            except:
                print ""
            
            try:
                message = message.replace("%delivery_time%",deliveryTime)
            except:
                print ""
            
            try:
                message = message.replace("%delivery_type%","\n1. Delivery \n2. Pickup\n")
            except:
                print ""
            
        try:
            message = message.replace("%business_name%",businessName)
        except:
            print ""
        try:
            message = message.replace("%mob_number%",formatted_phone_number)
        except:
            print ""
        
        return message
    
    def order_update_status(self,data):
        response = {}
        
        try:
            athentication = base64.b64decode(Headers()['Authentication'])
            i = athentication.split(':')
            username = i[0]
            password = i[1]
                
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            count = db.get_count('users',where,countValues)
               
            if count ==0:    
                response['status']  = "Failure"
                response['message'] = "Please try with valid user name and password."
                return response
            
            order_id=""
            order_status=""
            
            what="userid,user_type"
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            user_detail=db.get_all('users',what,where,countValues)
            owner_id=user_detail[0]['userId']
            user_type=user_detail[0]['userType']
            
            try:
                order_id = data['orderId']
                status = data['status']
            except:
                response['status']  = "Failure"
                response['message'] = "Please try Again with valid post fields."
                return response
                
            
            """cehck Valid order_id"""
            if data['orderId']:
                order_id = data['orderId']
                where = "Where order_id = %(order_id)s"
                countValues = {'order_id': (order_id)}
                
                if user_type == "business_owner":
                    where += " AND owner_id = %(owner_id)s"
                    countValues.update({'owner_id': (owner_id)})
            
                count = db.get_count('orders',where,countValues)
               
                if count ==0:
                    response['status']  = "Failure"
                    response['message'] = "Please try Again with valid orderId."
                    return response
                
                    """cehck allowed status"""
                if data['status']:
                    order_status=data['status']
                    valid_status = self.check_valid_status(order_id, order_status)
                    
                    if valid_status["status"] == "Failure":
                        response['status']  = "Failure"
                        response['message'] = valid_status["message"]
                        return response
                else:
                    response['status']  = "Failure"
                    response['message'] = "Please try with valid POST data."
                    return response
            
                
                if order_status == "open":
                    self.change_status(order_id, order_status)
                
                elif order_status == "closed":
                    self.change_status(order_id, order_status)
                
                elif order_status == "archive":
                    self.change_status(order_id, order_status)
                else:
                    
                    """Get Necessary Fields for tables"""
                    where = ""
                    what = "c.customer_token, c.default_paymethod_token,o.total_amount"
                    where = "WHERE o.order_id = %(order_id)s and o.user_number = c.mobile_number"
                    countValues = {'order_id': (order_id)}
                    customer_detail = db.get_all('orders o, customers c',what,where,countValues)
                    customer_token  =   customer_detail[0]['customerToken']
                    default_paymethod_token =   customer_detail[0]['defaultPaymethodToken']
                    totalAmount =   customer_detail[0]['totalAmount']
                    
                    result = self.transaction("disburse", customer_token, default_paymethod_token, totalAmount)
                    if result != "Failure":
                        
                        if result['response']['response_code']=='A01':
                            self.save_transaction_detail(result, "cancel_order", order_id)
                            self.change_status(order_id, order_status)
                        else:
                            response['status']  = "Failure"
                            response['message'] = "Customer Payment transaction issue. Please check payment method."
                            return response
                    else:    
                        response['status']  = "Failure"
                        response['message'] = "Customer Payment transaction issue. Please check payment method."
                        return response
                
                if order_status != "archive":
                    what = "user_number,owner_id"
                    where = "WHERE order_id = %(order_id)s"
                    countValues = {'order_id': (order_id)}
                    customer_detail = db.get_all('orders',what,where,countValues)
                    userMobileNumber  =   customer_detail[0]['userMobileNumber']
                    owner_id  =   customer_detail[0]['ownerId']
                    
                    
                    if order_status == "cancel":
                        system_name = "order_manually_cancel"
                    else:
                        system_name = "order_manually_update"
                    
                    message_detail = self.custom_message(system_name)
                    message = message_detail[0]['messageText']
                    message = message.replace("%status%",order_status)
                    msg_to = userMobileNumber
                    message = self.replace_variables(message, owner_id, order_id)
                    
                    data = {}
                    data['message']=message;
                    data['message_id']=message_detail[0]['defaultMessageId']
                    data['message_type'] = message_detail[0]['messageType']
                    data['table_name'] = "custom_default_messages";
                    data['owner_id']=owner_id
                    data['order_id']=order_id
                    data['msg_to']=msg_to
                    data['status']="sent"
                    data['order_type']="order"
                    result = db.create_log(data)
                    if result == "Failure":
                        print "sms log not created"
            
            
                    msg_from = "+16193910014"
                    try:
                        db.sms_send(msg_to, msg_from, message)
                    except:
                        print "sms not sent to customer"
                        
                
                response['status']  = "Success"
                response['message'] = "Status has been updated Successfully"
                return response
                
             
        except:
            response['status']  = "Failure"
            response['message'] = "Exception Error."
            return response
             
        
     
    def transaction(self,transaction_type,customer_token,default_paymethod_token,amount):
        
        try: 
          
            if len(customer_token)<1 or len(default_paymethod_token)<1:
                return "Failure"
            
            service_url = url+"accounts/"+AccountID+"/locations/"+LocationID+"/transactions"
            
            data = {}
            data["action"]=transaction_type
            data["customer_token"]=customer_token
            data["paymethod_token"]=default_paymethod_token
            data["authorization_amount"]=amount
            params = json.dumps(data)
            
            req = urllib2.Request(service_url,params)
            req.add_header("Authorization", auth_token)
            req.add_header("X-Forte-Auth-Account-Id", AccountID)
            req.add_header("Content-type", "application/json")
#           check any type of error  
            transaction_error = 0
                      
            try: 
                response = urllib2.urlopen(req)
            except urllib2.HTTPError, e:
                transaction_error = 1
                print response
                print e.code
            except urllib2.URLError, e:
                transaction_error = 1
                print "d2"
                checksLogger.error('URLError = ' + str(e.reason))
            except httplib.HTTPException, e:
                transaction_error = 1
                print "d3"
                checksLogger.error('HTTPException')
            except Exception:
                transaction_error = 1
                print "d4"
                import traceback
                checksLogger.error('generic exception: ' + traceback.format_exc())
            
#             if error in transaction return responce
            
            if  transaction_error == 1:
                 return "Failure"
            
            clientid = response.read()
            response.close()
            
            if len(clientid) > 0:
                result = json.loads(clientid)
                return result
        except:
            return "Failure"       
    
    
    def get_amount(self,order_id,owner_id,express_products_amount=None):
        
        what="tax_rate,delivery_charge,convenience_charge_customer"
        where = "WHERE userid = %(owner_id)s"
        countValues = {'owner_id': (owner_id)}
        user_detail=db.get_all('user_rules',what,where,countValues)
        
        tax_rate=user_detail[0]['taxRate']
        deliveryCharge=user_detail[0]['deliveryCharge']
        convenienceChargeCustomer=user_detail[0]['convenienceChargeCustomer']
        
       
        what="base_price,product_tax,quantity"
        where = "WHERE order_id = %(order_id)s"
        countValues = {'order_id': (order_id)}
        order_details=db.get_all('order_details',what,where,countValues)
        amount = float('0.00')
        for single in order_details: 
            obj = single

            base_price = obj['productBasePrice']
            product_tax = obj['productTax']
            quantity = obj['quantity']
            
            tax_rate = float(product_tax)/100 * float(base_price)* quantity
            amount_with_tax =  tax_rate + float(base_price)* quantity
            amount_with_tax =  format(float(amount_with_tax), '.2f')
            amount = amount + float(amount_with_tax)
       
        amount = amount + float(deliveryCharge) +float(convenienceChargeCustomer)
        return amount
       
       
            
    def check_transaction(self, transaction_type, amount, order_status, order_id, owner_number, owner_uniquecode, customer_number, result):
      
        if result['response']['response_code']=='A01':
            reverse_transaction_id =   result['transaction_id']
            reverse_authorization_code =   result['authorization_code']
            send_message = "Your order# " +order_id+" is updated by "+owner_uniquecode+".\n"+" Now order status is '"+order_status+"'"
                
            now  = datetime.datetime.now()
            date = now.strftime("%Y-%m-%d")
            currentdate = now.strftime("%Y-%m-%d %H:%M:%S")    
            message = ""
            if transaction_type == "disburse":
                where = "WHERE order_id = %(order_id)s"
                new_values = "is_reverse='1',date_updated = %(date_updated)s,status = %(status)s,reverse_transaction_id = %(reverse_transaction_id)s,reverse_authorization_code = %(reverse_authorization_code)s"
                updateValues = {'status':(order_status),'order_id':(order_id),'date_updated':(currentdate),'reverse_transaction_id':(reverse_transaction_id),'reverse_authorization_code':(reverse_authorization_code)}
                db.update_query('orders', new_values,where,updateValues)
                message = "Orders has been removed Successfully"
                send_message += "\n$"+amount+" tranferred back to your account.";
                
            else:
                where = "WHERE order_id = %(order_id)s"
                new_values = "date_updated = %(date_updated)s,status = %(status)s,transaction_id = %(reverse_transaction_id)s, authorization_code = %(reverse_authorization_code)s"
                updateValues = {'status':(order_status),'order_id':(order_id),'date_updated':(currentdate),'reverse_transaction_id':(reverse_transaction_id),'reverse_authorization_code':(reverse_authorization_code)}
                db.update_query('orders', new_values,where,updateValues)
                message = "Orders has been open Successfully"
                send_message += "\n$"+amount+" Amount charged from your's account.";
              
                 
            send_message += "\n For further information please contact "+owner_uniquecode+" at "+owner_number
            result = twilio_client.messages.create(
                                                   body = send_message,
                                                   to = customer_number,
                                                   from_= twilio_number) 
        
            return message
        
        else:
            return "Failure"        
        
                     
    def get_all_products(self):
        response  = {}
        
        try:
            athentication = base64.b64decode(Headers()['Authentication'])
            i = athentication.split(':')
            username = i[0]
            password = i[1]
            
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            count = db.get_count('users',where,countValues)
           
            if count ==0:  
                return response  
                response['status']  = "Failure"
                response['message'] = "Please try with valid user name and password."
                return response
            what="userid"
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            user_detail=db.get_all('users',what,where,countValues)
            owner_id=user_detail[0]['userId']
            
            what="p.product_name,p.product_id"
            where = "WHERE c.userid = %(userid)s and p.category_id = c.category_id"
            countValues = {'userid': (owner_id)}
            result = db.get_all('products p, categories c',what,where,countValues)
            response['status']  = "Success"
            response['data'] = result
            
            return response
        
        
        except:
            response['status']  = "Failure"
            response['message'] = "Exception Error."
            return response
    
    def calculate_express_tax(self,data):
        productBasePrice = data['productBasePrice']
        productTax = data['productTax']
        quantity = data['quantity']
                   
        tax_rate = float(productTax)/100 * float(productBasePrice)* float(quantity)
      
        amount_with_tax =  tax_rate + float(productBasePrice)* float(quantity)
        amount_with_tax =  format(float(amount_with_tax), '.2f')
        return amount_with_tax
  
    def check_max_amount(self,order_id,total_amount):
        
        data  = {}
        what="r.max_amount, r.amount_per_day, r.userid, o.user_number,o.total_amount"
        where = "WHERE o.order_id = %(order_id)s and o.owner_id = r.userid"
        countValues = {'order_id': (order_id)}
        result = db.get_all('user_rules r, orders o',what,where,countValues)
        
        userMobileNumber = result[0]['userMobileNumber'] 
        amountPerDay = float(result[0]['amountPerDay']) 
        userId = result[0]['userId'] 
        maxAmount = float(result[0]['maxAmount']) 
        totalAmount = float(result[0]['totalAmount']) 
        
        tatalOrderAmount = total_amount + float(totalAmount)
        
        if maxAmount <= tatalOrderAmount:
            data['status'] = "Failure"
            data['message'] = "Can not add item due to max amount limit"
            return data
        
        now  = datetime.datetime.now()
        currentdate = now.strftime("%Y-%m-%d")
          
        what="sum(total_amount) as total_amount"
        where = "WHERE status = 'closed' and user_number = %(userMobileNumber)s and owner_id = %(owner_id)s and date_updated LIKE %(currentdate)s"
        countValues = {'owner_id': (userId),'userMobileNumber': (userMobileNumber),'currentdate': (currentdate)+'%'}
        result = db.get_all('orders',what,where,countValues)
        
        today_amount = result[0]['totalAmount']
        
        if today_amount != None:
            tatalOrderAmount = total_amount + float(today_amount)
        else:
            tatalOrderAmount = total_amount
            
        if amountPerDay <= tatalOrderAmount:
            data['status'] = "Failure"
            data['message'] = "Can not add item, Because per order amount limit"
            return data
        
        data['status'] = "Success"
        data['message'] = "can Add"
        return data
        
    def check_min_amount(self,order_id,total_amount):
        
        data  = {}
        what="r.min_amount, o.total_amount"
        where = "WHERE o.order_id = %(order_id)s and o.owner_id = r.userid"
        countValues = {'order_id': (order_id)}
        result = db.get_all('user_rules r, orders o',what,where,countValues)
        
        minAmount = float(result[0]['minAmount']) 
        totalAmount = float(result[0]['totalAmount']) 
        tatalOrderAmount = float(totalAmount) - total_amount 
        
        if minAmount >= tatalOrderAmount:
            data['status'] = "Failure"
            data['message'] = "Can not remove item, Because per order amount limit"
            return data
        
        data['status'] = "Success"
        data['message'] = "can Add"
        return data
    
    def add_products(self,data):
        
        response = {}
        try:
            athentication = base64.b64decode(Headers()['Authentication'])
            i = athentication.split(':')
            username = i[0]
            password = i[1]
            
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            count = db.get_count('users',where,countValues)
          
            if count ==0:  
                response['status']  = "Failure"
                response['message'] = "Please try with valid user name and password."
                return response    
            
            try:
                order_id = data['orderId']
                product_id = data['productId']
                quantity = data['quantity']
            except:
                response['status']  = "Failure"
                response['message'] = "Please try again with valid post fields"
                return response
            
            
           
            if  order_id.isdigit() and product_id.isdigit() and quantity.isdigit():
                print "post data is ok"
            else:
                response['status']  = "Failure"
                response['message'] = "Please try with valid Data field."
                return response
         
            
            what="userid,user_type"
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            user_detail=db.get_all('users',what,where,countValues)
            owner_id=user_detail[0]['userId']
            user_type=user_detail[0]['userType']
           
            
#             check order id is valid
            
            where = "Where order_id = %(order_id)s"
            countValues = {'order_id': (order_id)}
                
            if user_type == "business_owner":
                where += " AND owner_id = %(owner_id)s"
                countValues.update({'owner_id': (owner_id)})
        
            count = db.get_count('orders',where,countValues)
            if count ==0:
                response['status']  = "Failure"
                response['message'] = "Please try Again with valid orderId."
                return response
            
            where += " AND status = 'open'"
            count = db.get_count('orders',where,countValues)
            if count ==0:
                response['status']  = "Failure"
                response['message'] = "Sorry can not edit. Because order status is not open"
                return response
            
            
                
#           get user number and owner id  
            what = "user_number,owner_id,total_amount"
            where = "WHERE order_id = %(order_id)s"
            countValues = {'order_id': (order_id)}
            customer_detail = db.get_all('orders',what,where,countValues)
            userMobileNumber  =   customer_detail[0]['userMobileNumber']
            owner_id  =   customer_detail[0]['ownerId']
            totalAmount  =   customer_detail[0]['totalAmount']
                    
                    
#             check product exists or not
            
            what = "p.product_base_price,p.product_name,p.product_tax"
            where = "WHERE c.userid = %(owner_id)s and c.category_id = p.category_id and p.product_id = %(product_id)s"
            countValues = {'owner_id': (owner_id),'product_id': (product_id)}
            product_detail = db.get_all('products p,categories c',what,where,countValues)
            
            if not len(product_detail):
                response['status']  = "Failure"
                response['message'] = "Please try Again with valid productId."
                return response
            
            
            productBasePrice = product_detail[0]['productBasePrice']
            productTax = product_detail[0]['productTax']
            productName = product_detail[0]['productName']
            if productTax == "1":
                what = "tax_rate"
                where = "WHERE userid = %(owner_id)s"
                countValues = {'owner_id': (owner_id)}
                product_detail = db.get_all('user_rules',what,where,countValues)
                productTax = product_detail[0]['taxRate']
                
            else:
                productTax = "0.00"
            
            data = {}
            data['productBasePrice'] = productBasePrice
            data['productTax'] = productTax
            data['productName'] = productName
            data['quantity'] = quantity
            amount_with_tax = self.calculate_express_tax(data)
            tatalOrderAmount = float(amount_with_tax)
            
            validate_max_amount = self.check_max_amount(order_id,tatalOrderAmount)
            if validate_max_amount['status'] == "Failure":
                response['status']  = "Failure"
                response['message'] = "Can not add item due to max amount limit"
                return response
            
            what = "c.customer_token, c.default_paymethod_token"
            where = "WHERE o.order_id = %(order_id)s and o.user_number = c.mobile_number"
            countValues = {'order_id': (order_id)}
            customer_detail = db.get_all('orders o, customers c',what,where,countValues)
            customer_token  =   customer_detail[0]['customerToken']
            default_paymethod_token =   customer_detail[0]['defaultPaymethodToken']
                    
            result = self.transaction("disburse", customer_token, default_paymethod_token, tatalOrderAmount)
            
            if result != "Failure":
                  
                if result['response']['response_code']=='A01':
                    self.save_transaction_detail(result, "add_item", order_id)
               
                else:
                    response['status']  = "Failure"
                    response['message'] = "Customer Payment transaction issue. Please check payment method."
                    return response
            else:    
                response['status']  = "Failure"
                response['message'] = "Customer Payment transaction issue. Please check payment method."
                return response
#                 
            item_amount = tatalOrderAmount
            tatalOrderAmount = tatalOrderAmount + float(totalAmount)
            
            now  = datetime.datetime.now()
            currentdate = now.strftime("%Y-%m-%d %H:%M:%S")    
                    
            what="order_detail_id,quantity"
            where = "WHERE product_id = %(product_id)s and order_id = %(order_id)s"
            countValues = {'product_id': (product_id),'order_id': (order_id)}
            product_exist = db.get_all('order_details',what,where,countValues)
            quantity =  int(quantity)
               
            if len(product_exist)>0:
                quantity_exit = product_exist[0]["quantity"] 
                quantity_exit =  int(quantity_exit)
                quantity = quantity + quantity_exit
                order_detail_id = product_exist[0]['orderDetailId']

                where = "WHERE order_detail_id = %(order_detail_id)s"
                new_values = "date_updated = %(date_updated)s,quantity = %(quantity)s"
                updateValues = {'order_detail_id':(order_detail_id),'date_updated':(currentdate),'quantity':(quantity)}
                db.update_query('order_details', new_values,where,updateValues)
              
            else:
                column = ['order_id','product_id','base_price','product_tax','quantity','date_created','date_updated']
                value = [order_id,product_id,productBasePrice,productTax,quantity,currentdate,currentdate]
                result = db.insert_query('order_details',column,value)
                   
            where = "WHERE order_id = %(order_id)s"
            new_values = "date_updated = %(date_updated)s,total_amount = %(OrderAmount)s"
            updateValues = {'order_id':(order_id),'OrderAmount':(tatalOrderAmount),'date_updated':(currentdate)}
            db.update_query('orders', new_values,where,updateValues)
                    
            message_detail = self.custom_message("product_add_message")
            message = message_detail[0]['messageText']
            quantity = data['quantity']
            quantity = str(quantity)
            item_amount = str(item_amount)
            message = message.replace("%product_added%",productName+"\n")
            message = message.replace("%quantity%",quantity+"\n")
            message = message.replace("%product_amount%",item_amount)
            msg_to = userMobileNumber
            message = self.replace_variables(message, owner_id, order_id)
                    
            data = {}
            data['message']=message;
            data['message_id']=message_detail[0]['defaultMessageId']
            data['message_type'] = message_detail[0]['messageType']
            data['table_name'] = "custom_default_messages";
            data['owner_id']=owner_id
            data['order_id']=order_id
            data['msg_to']=msg_to
            data['status']="sent"
            data['order_type']="order"
            result = db.create_log(data)
            if result == "Failure":
                print "sms log not created"
            
            
            msg_from = "+16193910014"
            try:
                db.sms_send(msg_to, msg_from, message)
            except:
                print "sms not sent to customer"
                        
                
            response['status']  = "Success"
            response['message'] = "Item has been Added Successfully"
            return response
                  
        except:
            response['status']  = "Failure"
            response['message'] = "Exception Error."
            return response
         
                
#     def remove_item_from_order(self,orderid,detailid):
#         
#         responses = {}
#         response = {}
#          
#         try:
#             athentication = base64.b64decode(Headers()['Authentication'])
#             i = athentication.split(':')
#             username = i[0]
#             password = i[1]
#             
#             where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
#             countValues = {'username': (username), 'password': (password)}
#             count = db.get_count('users',where,countValues)
#           
#             if count ==0:  
#                 response['status']  = "Failure"
#                 response['message'] = "Please try with valid user name and password."
#                 return response    
#             what="userid,user_type"
#             where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
#             countValues = {'username': (username), 'password': (password)}
#             user_detail=db.get_all('users',what,where,countValues)
#             owner_id=user_detail[0]['userId']
#             user_type=user_detail[0]['userType']
#             admin_type = 0
#            
#             if user_type == "sys_admin":
#                 admin_type = 1
#              
#             order_id = orderid
#             order_detail_id = detailid
#            
#             if  order_id.isdigit() and order_detail_id.isdigit():
#                 print "post data is ok"
#             else:
#                 response['status']  = "Failure"
#                 response['message'] = "Please try with valid orderId and detailid field."
#                 return response
#             #get base price
#             what="c.customer_token,c.default_paymethod_token"
#             if admin_type == 1:
#                 where = "WHERE o.order_id = %(order_id)s and o.user_number = c.mobile_number"
#                 countValues = {'order_id': (order_id)}
#             else:
#                 where = "WHERE o.owner_id = %(owner_id)s and o.order_id = %(order_id)s and o.user_number = c.mobile_number"
#                 countValues = {'order_id': (order_id),'owner_id': (owner_id)}
#             
#             customer_detail = db.get_all('customers c, orders o',what,where,countValues)
#             default_paymethod_token =   customer_detail[0]['defaultPaymethodToken']
#             customer_token  =   customer_detail[0]['customerToken']
#             if len(customer_token)<1 or len(default_paymethod_token)<1:
#                 response['status']  = "Failure"
#                 response['message'] = "Customer Payment transaction issue. Please check payment method."
#                 return response
#            
#             what="d.*"
#             if admin_type == 1:
#                 where = "WHERE o.order_id = %(order_id)s and o.order_id = d.order_id and d.order_detail_id = %(order_detail_id)s"
#                 countValues = {'order_id': (order_id),'order_detail_id': (order_detail_id)}
#             else:
#                 where = "WHERE o.owner_id = %(owner_id)s and o.order_id = %(order_id)s and o.order_id = d.order_id and d.order_detail_id = %(order_detail_id)s"
#                 countValues = {'owner_id': (owner_id), 'order_id': (order_id),'order_detail_id': (order_detail_id)}
#              
#             prodcut_detail = db.get_all('order_details d, orders o',what,where,countValues)
#             quantity = prodcut_detail[0]['quantity']
#             productBasePrice = prodcut_detail[0]['productBasePrice']
#             
#             productBasePrice = float(productBasePrice)
#             quantity = float(quantity)
#             amount = productBasePrice * quantity
#            
#             
#             what="tax_rate"
#             if admin_type == 1:
#                 
#                 what="owner_id"
#                 where = "WHERE order_id = %(order_id)s"
#                 countValues = {'order_id': (order_id)}
#                 prodcut_detail = db.get_all('orders',what,where,countValues)
#                 business_owner_id = prodcut_detail[0]["ownerId"]
#               
#                 what="tax_rate"
#                 where = "WHERE userid = %(business_owner_id)s"
#                 countValues = {'business_owner_id': (business_owner_id)}
#             else:
#                 where = "WHERE userid = %(owner_id)s"
#                 countValues = {'owner_id': (owner_id)}
#             
#             user_detail=db.get_all('user_rules',what,where,countValues)
#             tax_rate=user_detail[0]['taxRate']
#             tax_rate = float(tax_rate)/100 * float(amount)
#             amount = float(amount) + float(tax_rate)
# 
# 
#             service_url = url+"accounts/"+AccountID+"/locations/"+LocationID+"/transactions"
#             data = {}
#             data["action"]="disburse"
#             data["customer_token"]=customer_token
#             data["paymethod_token"]=default_paymethod_token
#             data["authorization_amount"]=amount
#             params = json.dumps(data)
#             
#             req = urllib2.Request(service_url,params)
#             req.add_header("Authorization", auth_token)
#             req.add_header("X-Forte-Auth-Account-Id", AccountID)
#             req.add_header("Content-type", "application/json")
# #           check any type of error  
#             transaction_error = 0
#                       
#             try: 
#                 response = urllib2.urlopen(req)
#             except urllib2.HTTPError, e:
#                 transaction_error = 1
#                 print response
#                 print e.code
#             except urllib2.URLError, e:
#                 transaction_error = 1
#                 print "d2"
#                 checksLogger.error('URLError = ' + str(e.reason))
#             except httplib.HTTPException, e:
#                 transaction_error = 1
#                 print "d3"
#                 checksLogger.error('HTTPException')
#             except Exception:
#                 transaction_error = 1
#                 print "d4"
#                 import traceback
#                 checksLogger.error('generic exception: ' + traceback.format_exc())
#             
# #             if error in transaction return responce
#             if  transaction_error == 1:
#                 response['status']  = "Failure"
#                 response['message'] = "Customer Payment transaction issue. Please check payment method."
#                 return response
#             
#             clientid = response.read()
#             response.close()
#             if len(clientid) > 0:
#                 result = json.loads(clientid)
# #               if status is success then ok else return error responce   
#                 if result['response']['response_code']=='A01':
# #               
#                     where = "WHERE order_detail_id = %(order_detail_id)s"
#                     updateValues = {'order_detail_id':(order_detail_id)}
#                     db.delete_query('order_details',where,updateValues)
#                 
#                     responses['status']  = "Success"
#                     responses['data'] =  "deleted sccessfully"
#                     return responses
#                     
#                 else:  
#                     response['status']  = "Failure"
#                     response['message'] = result['response']['response_desc']+"Please check payment method."
#                     return response
#                 
#             else:
#                response['status']  = "Failure"
#                response['message'] = result['response']['response_desc']+"Please check payment method."
#                return response
#       
#         except:
#             response['status']  = "Failure"
#             response['message'] = "Exception Error."
#             return response 
         
        
        
        
    def remove_item_from_order(self,orderid=None,detailid=None,data=None):
        
        response = {}
         
        try:
            athentication = base64.b64decode(Headers()['Authentication'])
            i = athentication.split(':')
            username = i[0]
            password = i[1]
            
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            count = db.get_count('users',where,countValues)
          
            if count ==0:  
                response['status']  = "Failure"
                response['message'] = "Please try with valid user name and password."
                return response
            
            what="userid,user_type"
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            user_detail=db.get_all('users',what,where,countValues)
            owner_id=user_detail[0]['userId']
            user_type=user_detail[0]['userType']
            
            
            if orderid != None:
                data = {}
                data['orderId'] = orderid
                data['detailIds'] = detailid
                
            
            try:
                order_id = data['orderId']
                order_detail_list = data['detailIds']
            except:
                response['status']  = "Failure"
                response['message'] = "Please try again with valid post fields"
                return response
            
            
            if  order_id.isdigit():
                    print "post data is ok"
            else:
                response['status']  = "Failure"
                response['message'] = "Please try with valid orderId."
                return response
                
            detailIds = order_detail_list.split(',')
            validate_id = 1
            
#             Check detail id are valid or not
            for order_detail_id in detailIds:
                
                if  order_detail_id.isdigit():
                    print "post data is ok"
                else:
                    print "invalid post data"
                    response['status']  = "Failure"
                    response['message'] = "Please try with valid orderId and detailIds field."
                    return response
                
                where = "WHERE d.order_detail_id = %(order_detail_id)s AND d.order_id = %(order_id)s"
                countValues = {'order_detail_id': (order_detail_id), 'order_id': (order_id)}
                table = "order_details d"
                if user_type == "business_owner":
                    where += "AND d.order_id = o.order_id AND o.owner_id = %(owner_id)s"
                    countValues.update({'owner_id': (owner_id)})
                    table += ",orders o"
                    
                count = db.get_count(table,where,countValues)
                if(count==0):
                    validate_id = 0
            
            if validate_id == 0:
                response['status']  = "Failure"
                response['message'] = "Please try with valid orderId and detailId field."
                return response
            
            
            where = "Where order_id = %(order_id)s"
            countValues = {'order_id': (order_id)}
                
            if user_type == "business_owner":
                where += " AND owner_id = %(owner_id)s"
                countValues.update({'owner_id': (owner_id)})
        
            where += " AND status = 'open'"
            count = db.get_count('orders',where,countValues)
            if count ==0:
                response['status']  = "Failure"
                response['message'] = "Sorry can not edit. Because order status is not open"
                return response
        
            
#             check all item length
            detailIds_count = len(detailIds)
            
            where = "WHERE order_id = %(order_id)s"
            countValues = {'order_id': (order_id)}
            count = db.get_count('order_details',where,countValues)
            
            if detailIds_count == int(count):
                response['status']  = "Failure"
                response['message'] = "Sorry Can not remove all Items from order."
                return response
            
            
#           getting total amount of remove items  
            product_ids = {}
            index = 0
            total_remove_amount = 0.00
            for order_detail_id in detailIds:
                what="quantity,base_price,product_tax,product_id"
                where = "WHERE order_detail_id = %(order_detail_id)s"
                countValues = {'order_detail_id': (order_detail_id)}
                prodcut_detail = db.get_all('order_details',what,where,countValues)
                existing_quantity = prodcut_detail[0]['quantity']
                productBasePrice = prodcut_detail[0]['productBasePrice']
                productTax = prodcut_detail[0]['productTax']
                product_ids[index] = prodcut_detail[0]['productId']
                index += 1
                data = {}
                data['productBasePrice'] = productBasePrice
                data['productTax'] = productTax
                data['quantity'] = int(existing_quantity)
                
                amount_with_tax = self.calculate_express_tax(data)
                total_remove_amount = total_remove_amount + float(amount_with_tax)
            
            
            what = "total_amount,owner_id,user_number"
            where= "where order_id = %(order_id)s"
            allValues = {'order_id':(order_id)}
            result = db.get_all('orders',what,where,allValues)
            totalAmount = float(result[0]['totalAmount'])
            owner_id = result[0]['ownerId']
            userMobileNumber = result[0]['userMobileNumber']
            remaining_amount = totalAmount - total_remove_amount
            
            validate_amount = self.check_min_amount(order_id,total_remove_amount)
            if validate_amount['status'] == "Failure":
                response['status']  = "Failure"
                response['message'] = "Can not remove item due to min amount limit"
                return response
          
             
            what="c.customer_token,c.default_paymethod_token"
            where = "WHERE o.order_id = %(order_id)s and o.user_number = c.mobile_number"
            countValues = {'order_id': (order_id)}
            customer_detail = db.get_all('customers c, orders o',what,where,countValues)
            default_paymethod_token =   customer_detail[0]['defaultPaymethodToken']
            customer_token  =   customer_detail[0]['customerToken']
            
            
            result = self.transaction("disburse", customer_token, default_paymethod_token, total_remove_amount)
            if result != "Failure":
               
                if result['response']['response_code']=='A01':
                    self.save_transaction_detail(result, "remove_item", order_id)
                else:
                    response['status']  = "Failure"
                    response['message'] = "Customer Payment transaction issue. Please check payment method."
                    return response
            else:    
                response['status']  = "Failure"
                response['message'] = "Customer Payment transaction issue. Please check payment method."
                return response
# 
            for order_detail_id in detailIds:
                where = "WHERE order_detail_id = %(order_detail_id)s"
                updateValues = {'order_detail_id':(order_detail_id)}
                db.delete_query('order_details',where,updateValues)

            index = 0
            productName = {}
            for product_id in product_ids:
                what="product_name"
                where = "WHERE product_id = %(product_id)s"
                countValues = {'product_id': (product_ids[index])}
                prodcut_detail = db.get_all('products',what,where,countValues)
                productName[prodcut_detail[0]['productName']] = prodcut_detail[0]['productName']
                index += 1
            
            product_name = ' , '.join([str(i) for i in productName])
                
            
            
            now  = datetime.datetime.now()
            currentdate = now.strftime("%Y-%m-%d %H:%M:%S")    
                    
            where = "WHERE order_id = %(order_id)s"
            new_values = "date_updated = %(date_updated)s,total_amount = %(remaining_amount)s"
            updateValues = {'order_id':(order_id),'remaining_amount':(remaining_amount),'date_updated':(currentdate)}
            db.update_query('orders', new_values,where,updateValues)
            
                    
            message_detail = self.custom_message("product_delete_message")
            message = message_detail[0]['messageText']
            total_remove_amount = str(total_remove_amount)
            message = message.replace("%product_added%",product_name+"\n")
            message = message.replace("Qty: %quantity%","")
            message = message.replace("%product_amount%",total_remove_amount)
            
            
            msg_to = userMobileNumber
            message = self.replace_variables(message, owner_id, order_id)
                    
            data = {}
            data['message']=message;
            data['message_id']=message_detail[0]['defaultMessageId']
            data['message_type'] = message_detail[0]['messageType']
            data['table_name'] = "custom_default_messages";
            data['owner_id']=owner_id
            data['order_id']=order_id
            data['msg_to']=msg_to
            data['status']="sent"
            data['order_type']="order"
            result = db.create_log(data)
            if result == "Failure":
                print "sms log not created"
            
            
            msg_from = "+16193910014"
            try:
                db.sms_send(msg_to, msg_from, message)
            except:
                print "sms not sent to customer"
                
            response['status']  = "Success"
            response['message'] = "Item has been Removed Successfully"
            return response

        except:
            response['status']  = "Failure"
            response['message'] = "Exception Error."
            return response 
         
    def get_messages_log(self,order_id):
        
        response = {}
         
        try:
            
            athentication = base64.b64decode(Headers()['Authentication'])
            i = athentication.split(':')
            username = i[0]
            password = i[1]
            
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            count = db.get_count('users',where,countValues)
          
            if count ==0:  
                response['status']  = "Failure"
                response['message'] = "Please try with valid user name and password."
                return response    
            
            if  order_id.isdigit():
                print "post data is ok"
            else:
                response['status']  = "Failure"
                response['message'] = "Please try with valid orderId and detailid field."
                return response
            
            what="q.query, q.status, c.first_name, c.last_name, u.owner_uniquecode,u.business_name,DATE_FORMAT(q.date_created,'%%Y-%%m-%%d %%H:%%i:%%s') as date_created"
            where = "WHERE q.order_id = %(order_id)s and q.order_id = o.order_id and o.owner_id = u.userid and c.mobile_number = o.user_number"
            countValues = {'order_id': (order_id)}
            
            message_log=db.get_all('order_queries q, orders o, users u, customers c',what,where,countValues)
            
            response['status']  = "Success"
            response['data'] =  message_log
            return response
                    
               
      
        except:
            response['status']  = "Failure"
            response['message'] = "Exception Error."
            return response 
         
    def send_owner_message(self,data):
        
        response = {}
         
        try:
                athentication = base64.b64decode(Headers()['Authentication'])
                i = athentication.split(':')
                username = i[0]
                password = i[1]
                
                where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
                countValues = {'username': (username), 'password': (password)}
                count = db.get_count('users',where,countValues)
              
                if count ==0:  
                    response['status']  = "Failure"
                    response['message'] = "Please try with valid user name and password."
                    return response    
                
                what="userid"
                where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
                countValues = {'username': (username), 'password': (password)}
                user_detail=db.get_all('users',what,where,countValues)
                
                owner_id=user_detail[0]['userId']
                order_id = data['orderId']
                message = data['message']
                
                if  order_id.isdigit() and len(message)>1:
                    print "post data is ok"
                else:
                    response['status']  = "Failure"
                    response['message'] = "Please try with valid orderId and Message field should not empty."
                    return response
             
             
                where = "Where order_id = %(order_id)s"
                new_values = "is_query = 1"
                updateValues = {'order_id':(order_id)}
                db.update_query('orders', new_values,where,updateValues)
                
                what="user_number"
                order_detail=db.get_all('orders',what,where,updateValues)
                user_number = order_detail[0]['userMobileNumber']
               
        #       
                what="business_name"
                where = "Where userid = %(owner_id)s"
                updateValues = {'owner_id':(owner_id)}
                user_detail=db.get_all('users',what,where,updateValues)
                owner_uniquecode = user_detail[0]['businessName']
                
                send_message = "Query Message from "+owner_uniquecode+" for your order# "+order_id+"\n"
                send_message += message+"\n";
                send_message += "For reply please type 'query_"+order_id+": your_reply' like 'query_"+order_id+": yes i order this item.' and press send";
                 
                result = twilio_client.messages.create(
                                                        body = send_message,
                                                        to = user_number,    # Replace with your phone number
                                                        from_= twilio_number) # Replace with your Twilio number
                
                now  = datetime.datetime.now()
                currentdate = now.strftime("%Y-%m-%d %H:%M:%S")
                column = ['order_id','user_number','owner_id','query','status','date_created']
                value = [order_id,user_number,owner_id,message,'sent',currentdate]
                result = db.insert_query('order_queries',column,value)
               
                response['status']  = "Success"
                response['data'] =  "Message has been send successfully"
                return response
                
               
      
        except:
            response['status']  = "Failure"
            response['message'] = "Exception Error."
            return response          
       
    def change_item_quantity_from_order(self,detailid,newQuantity):
        responses = {}
        response = {}
         
        try:
            athentication = base64.b64decode(Headers()['Authentication'])
            i = athentication.split(':')
            username = i[0]
            password = i[1]
            
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            count = db.get_count('users',where,countValues)
          
            if count ==0:  
                response['status']  = "Failure"
                response['message'] = "Please try with valid user name and password."
                return response    
            what="userid,user_type"
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            user_detail=db.get_all('users',what,where,countValues)
            owner_id=user_detail[0]['userId']
            user_type=user_detail[0]['userType']
            admin_type = 0
           
            if user_type == "sys_admin":
                admin_type = 1
             
            order_detail_id = detailid
            quantity = newQuantity
            new_quantity = newQuantity
            
            """check valid inputs"""
            if  order_detail_id.isdigit() and quantity.isdigit():
                print "post data is ok"
            else:
                response['status']  = "Failure"
                response['message'] = "Please try with valid newQuantity and detailid field."
                return response
          
            if quantity == 0:
                response['status']  = "Failure"
                response['message'] = "Please try with valid newQuantity."
                return response
            
            quantity = int(newQuantity)
             
            where = "WHERE order_detail_id = %(order_detail_id)s"
            countValues = {'order_detail_id': (order_detail_id)}
            count = db.get_count('order_details',where,countValues)
            
            if count == 0:
                response['status']  = "Failure"
                response['message'] = "Please try with valid detailid."
                return response
           
            """Get Customers Tokens"""
            
            what="c.customer_token,c.default_paymethod_token, o.order_id,o.total_amount,o.owner_id,o.user_number"
            if admin_type == 1:
                where = "WHERE d.order_detail_id = %(order_detail_id)s and o.order_id = d.order_id and o.user_number = c.mobile_number"
                countValues = {'order_detail_id': (order_detail_id)}
            else:
                where = "WHERE o.owner_id = %(owner_id)s and d.order_detail_id = %(order_detail_id)s and o.order_id = d.order_id and o.user_number = c.mobile_number"
                countValues = {'order_detail_id': (order_detail_id),'owner_id': (owner_id)}
            
            customer_detail = db.get_all('customers c, orders o, order_details d',what,where,countValues)
            default_paymethod_token =   customer_detail[0]['defaultPaymethodToken']
            customer_token  =   customer_detail[0]['customerToken']
            order_id  =   customer_detail[0]['orderId']
            totalAmount  =   customer_detail[0]['totalAmount']
            owner_id  =   customer_detail[0]['ownerId']
            userMobileNumber  =   customer_detail[0]['userMobileNumber']
            order_id = str(order_id)
            
            if len(customer_token)<1 or len(default_paymethod_token)<1:
                response['status']  = "Failure"
                response['message'] = "Customer Payment transaction issue. Please check payment method."
                return response
           
            """get base price and quantity"""
            
            
            where = "Where order_id = %(order_id)s"
            countValues = {'order_id': (order_id)}
                
            if user_type == "business_owner":
                where += " AND owner_id = %(owner_id)s"
                countValues.update({'owner_id': (owner_id)})
        
            where += " AND status = 'open'"
            count = db.get_count('orders',where,countValues)
            if count ==0:
                response['status']  = "Failure"
                response['message'] = "Sorry can not edit. Because order status is not open"
                return response
        
            
            
            what="d.*"
            where = "WHERE d.order_detail_id = %(order_detail_id)s"
            countValues = {'order_detail_id': (order_detail_id)}
            prodcut_detail = db.get_all('order_details d',what,where,countValues)
            existing_quantity = prodcut_detail[0]['quantity']
            productBasePrice = prodcut_detail[0]['productBasePrice']
            productTax = prodcut_detail[0]['productTax']
          
            if quantity > int(existing_quantity):
                action = "sale"
                order_type = "edit_add_quantity"
                quantity = quantity - int(existing_quantity)
            elif quantity < int(existing_quantity):
                action = "disburse"
                order_type = "edit_remove_quantity"
                quantity = int(existing_quantity) - quantity
            else:
                responses['status']  = "Success"
                responses['data'] =  "Quantity Updated sccessfully"
                return responses
           
            data = {}
            data['productBasePrice'] = productBasePrice
            data['productTax'] = productTax
            data['quantity'] = quantity
            
            
            amount_with_tax = self.calculate_express_tax(data)
            amount_with_tax = float(amount_with_tax)
            
            if action == "sale":
                orderAmount = float(totalAmount) + amount_with_tax
                system_name = "product_edit_sale_message"
                
                validate_amount = self.check_max_amount(order_id,amount_with_tax)
                if validate_amount['status'] == "Failure":
                    response['status']  = "Failure"
                    response['message'] = "Can not edit item due to max amount limit"
                    return response
                
            else:
                orderAmount = float(totalAmount) - amount_with_tax
                system_name = "product_edit_disburse_message"
                
                validate_amount = self.check_min_amount(order_id,amount_with_tax)
                if validate_amount['status'] == "Failure":
                    response['status']  = "Failure"
                    response['message'] = validate_amount['message']
                    return response
            
                
            
            result = self.transaction(action, customer_token, default_paymethod_token, amount_with_tax)
             
            if result != "Failure":
                   
                if result['response']['response_code']=='A01':
                    self.save_transaction_detail(result, order_type, order_id)
                else:
                    response['status']  = "Failure"
                    response['message'] = "Customer Payment transaction issue. Please check payment method."
                    return response
            else:    
                response['status']  = "Failure"
                response['message'] = "Customer Payment transaction issue. Please check payment method."
                return response
#           


        
            now  = datetime.datetime.now()
            currentdate = now.strftime("%Y-%m-%d %H:%M:%S")    
            quantity = newQuantity
            
            where = "WHERE order_detail_id = %(order_detail_id)s"
            new_values = "date_updated = %(date_updated)s,quantity = %(quantity)s"
            updateValues = {'order_detail_id':(order_detail_id),'date_updated':(currentdate),'quantity':(quantity)}
            db.update_query('order_details', new_values,where,updateValues)
               
            where = "WHERE order_id = %(order_id)s"
            new_values = "date_updated = %(date_updated)s,total_amount = %(OrderAmount)s"
            updateValues = {'order_id':(order_id),'OrderAmount':(orderAmount),'date_updated':(currentdate)}
            db.update_query('orders', new_values,where,updateValues)
                     
            message_detail = self.custom_message(system_name)
            message = message_detail[0]['messageText']
            quantity = data['quantity']
            quantity = str(quantity)
            amount_with_tax = str(amount_with_tax)
            
            what = "product_id"
            where = "WHERE order_detail_id = %(order_detail_id)s"
            countValues = {'order_detail_id': (order_detail_id)}
            product_detail = db.get_all('order_details',what,where,countValues)
            product_id = product_detail[0]['productId']
           
            what = "product_name"
            where = "WHERE product_id = %(product_id)s"
            countValues = {'product_id': (product_id)}
            product_detail = db.get_all('products',what,where,countValues)
            productName = product_detail[0]['productName']
            message = message.replace("%product_added%",productName+"\n")
            message = message.replace("%quantity%",quantity+"\n")
            message = message.replace("%product_amount%",amount_with_tax+"\n")
            message = message.replace("%order_id%",order_id)
            msg_to = userMobileNumber
           
            message = self.replace_variables(message, owner_id, order_id)
                    
            data = {}
            data['message']=message;
            data['message_id']=message_detail[0]['defaultMessageId']
            data['message_type'] = message_detail[0]['messageType']
            data['table_name'] = "custom_default_messages";
            data['owner_id']=owner_id
            data['order_id']=order_id
            data['msg_to']=msg_to
            data['status']="sent"
            data['order_type']="order"
            result = db.create_log(data)
            if result == "Failure":
                print "sms log not created"
            
            
            msg_from = "+16193910014"
            try:
                db.sms_send(msg_to, msg_from, message)
            except:
                print "sms not sent to customer"
                        
                
            response['status']  = "Success"
            response['message'] = "Item has been Added Successfully"
            return response
               
             
        except:
            response['status']  = "Failure"
            response['message'] = "Exception Error."
            return response    
    
    
#     def remove_order(self,orderid):
#         
#         responses = {}
#         response = {}
#          
#         try:
#             athentication = base64.b64decode(Headers()['Authentication'])
#             i = athentication.split(':')
#             username = i[0]
#             password = i[1]
#             
#             where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
#             countValues = {'username': (username), 'password': (password)}
#             count = db.get_count('users',where,countValues)
#           
#             if count ==0:  
#                 response['status']  = "Failure"
#                 response['message'] = "Please try with valid user name and password."
#                 return response
#             
#             what="userid,user_type"
#             where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
#             countValues = {'username': (username), 'password': (password)}
#             user_detail=db.get_all('users',what,where,countValues)
#             owner_id=user_detail[0]['userId']
#             user_type=user_detail[0]['userType']
#             order_id = orderid
#             
#             if  order_id.isdigit():
#                 print "post data is ok"
#             else:
#                 response['status']  = "Failure"
#                 response['message'] = "Please try with valid orderId."
#                 return response
#             
#             where = "WHERE order_id = %(order_id)s"
#             countValues = {'order_id': (order_id)}
#             
#             if user_type != "sys_admin":
#                 where += " and owner_id = %(owner_id)s"
#                 countValues = {'order_id': (order_id),'owner_id': (owner_id)}
#             
#             countValues = {'order_id': (order_id),'owner_id': (owner_id)}
#             count = db.get_count('orders',where,countValues)
#             
#             if count == 0:
#                 response['status']  = "Failure"
#                 response['message'] = "Please try with valid orderId."
#                 return response
#                
#             """" get customer payment info"""    
#             what="c.customer_token,c.default_paymethod_token"
#             if user_type == "sys_admin":
#                 where = "WHERE o.order_id = %(order_id)s and o.user_number = c.mobile_number"
#                 countValues = {'order_id': (order_id)}
#             else:
#                 where = "WHERE o.owner_id = %(owner_id)s and o.order_id = %(order_id)s and o.user_number = c.mobile_number"
#                 countValues = {'order_id': (order_id),'owner_id': (owner_id)}
#                 
#             customer_detail = db.get_all('customers c, orders o',what,where,countValues)
#             default_paymethod_token =   customer_detail[0]['defaultPaymethodToken']
#             customer_token  =   customer_detail[0]['customerToken']
#             if len(customer_token)<1 or len(default_paymethod_token)<1:
#                 response['status']  = "Failure"
#                 response['message'] = "Customer Payment transaction issue. Please check payment method."
#                 return response
#              
#             """ Get total oder price """
#                
#             what="sum(base_price * quantity) as amount"
#             where = "WHERE order_id = %(order_id)s"
#             countValues = {'order_id': (order_id)}
#              
#             total_product_amount = db.get_all('order_details',what,where,countValues)
#             amount = total_product_amount[0]['amount']
#             
#             """if order have no item"""
#             if amount == None:
#                 now  = datetime.datetime.now()
#                 date = now.strftime("%Y-%m-%d")
#                 currentdate = now.strftime("%Y-%m-%d %H:%M:%S")
#                 
#                 where = "where order_id = %(order_id)s"    
#                 new_values = "date_updated = %(date_updated)s,status = 'cancel'"
#                 updateValues = {'order_id':(order_id),'date_updated':(currentdate)}
#                 db.update_query('orders', new_values,where,updateValues)
#                 
#                 responses['status']  = "Success"
#                 responses['data'] =  "Order has been Cancel sccessfully"
#                 return responses
#             
#             """ get tax rate of customer"""
#             
#             what="tax_rate,delivery_charge,convenience_charge_customer"
#             if user_type == "sys_admin":
#                 
#                 what="owner_id"
#                 where = "WHERE order_id = %(order_id)s"
#                 countValues = {'order_id': (order_id)}
#                 prodcut_detail = db.get_all('orders',what,where,countValues)
#                 business_owner_id = prodcut_detail[0]["ownerId"]
#               
#                 what="tax_rate,delivery_charge,convenience_charge_customer"
#                 where = "WHERE userid = %(business_owner_id)s"
#                 countValues = {'business_owner_id': (business_owner_id)}
#             else:
#                 where = "WHERE userid = %(owner_id)s"
#                 countValues = {'owner_id': (owner_id)}
#             
#             user_detail=db.get_all('user_rules',what,where,countValues)
#             tax_rate=user_detail[0]['taxRate']
#             deliveryCharge=user_detail[0]['deliveryCharge']
#             convenienceChargeCustomer=user_detail[0]['convenienceChargeCustomer']
#             tax_rate = float(tax_rate)/100 * float(amount)
#             amount = float(amount) + float(tax_rate) + float(deliveryCharge) + float(convenienceChargeCustomer)
#             
#             """ reverse transaction to customer """
#             service_url = url+"accounts/"+AccountID+"/locations/"+LocationID+"/transactions"
#             data = {}
#             data["action"]="disburse"
#             data["customer_token"]=customer_token
#             data["paymethod_token"]=default_paymethod_token
#             data["authorization_amount"]=amount
#             params = json.dumps(data)
#             
#             req = urllib2.Request(service_url,params)
#             req.add_header("Authorization", auth_token)
#             req.add_header("X-Forte-Auth-Account-Id", AccountID)
#             req.add_header("Content-type", "application/json")
#     #           check any type of error  
#             transaction_error = 0
#                       
#             try: 
#                 response = urllib2.urlopen(req)
#             except urllib2.HTTPError, e:
#                 transaction_error = 1
#                 print response
#                 print e.code
#             except urllib2.URLError, e:
#                 transaction_error = 1
#                 print "d2"
#                 checksLogger.error('URLError = ' + str(e.reason))
#             except httplib.HTTPException, e:
#                 transaction_error = 1
#                 print "d3"
#                 checksLogger.error('HTTPException')
#             except Exception:
#                 transaction_error = 1
#                 print "d4"
#                 import traceback
#                 checksLogger.error('generic exception: ' + traceback.format_exc())
#             
#     #             if error in transaction return responce
#             if  transaction_error == 1:
#                 response['status']  = "Failure"
#                 response['message'] = "Customer Payment transaction issue. Please check payment method."
#                 return response
#             
#             clientid = response.read()
#             response.close()
#             if len(clientid) > 0:
#                 result = json.loads(clientid)
#     #               if status is success then ok else return error responce   
#                 if result['response']['response_code']=='A01':
#                     
#                     now  = datetime.datetime.now()
#                     date = now.strftime("%Y-%m-%d")
#                     currentdate = now.strftime("%Y-%m-%d %H:%M:%S")
#                     
#                     reverse_transaction_id =   result['transaction_id']
#                     authorization_code =   result['authorization_code']
#                     where = "where order_id = %(order_id)s"    
#                     new_values = "date_updated = %(date_updated)s,status = 'cancel',is_reverse='1',reverse_transaction_id = %(reverse_transaction_id)s,reverse_authorization_code = %(authorization_code)s"
#                     updateValues = {'order_id':(order_id),'date_updated':(currentdate),'reverse_transaction_id':(reverse_transaction_id),'authorization_code':(authorization_code)}
#                     db.update_query('orders', new_values,where,updateValues)
#                
#                 else:  
#                     response['status']  = "Failure"
#                     response['message'] = result['response']['response_desc']+"Please check payment method."
#                     return response
#                 
#             else:
#                response['status']  = "Failure"
#                response['message'] = result['response']['response_desc']+"Please check payment method."
#                return response
#                
#             responses['status']  = "Success"
#             responses['data'] =  "Order has been Cancel sccessfully"
#             return responses
#                
#         except:
#             response['status']  = "Failure"
#             response['message'] = "Exception Error."
#             return response 
        
        
    def order_update_print(self,data):
        response = {}
         
        try:
            athentication = base64.b64decode(Headers()['Authentication'])
            i = athentication.split(':')
            username = i[0]
            password = i[1]
            
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            count = db.get_count('users',where,countValues)
          
            if count ==0:  
                response['status']  = "Failure"
                response['message'] = "Please try with valid user name and password."
                return response
            
            what="userid,user_type"
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            user_detail=db.get_all('users',what,where,countValues)
           
            
            owner_id=user_detail[0]['userId']
            order_id=data['orderId']
            
            where = "WHERE order_id = %(order_id)s AND owner_id = %(owner_id)s"
            countValues = {'order_id': (order_id), 'owner_id': (owner_id)}
            count = db.get_count('orders',where,countValues)
            if count == 0:
                response['status']  = "Failure"
                response['message'] = "Please try with valid orderId."
                return response 
            
            now  = datetime.datetime.now()
            date = now.strftime("%Y-%m-%d")
            currentdate = now.strftime("%Y-%m-%d %H:%M:%S")
            
            where = "WHERE order_id = %(order_id)s"
            new_values = "date_updated = %(date_updated)s,is_print = '1'"
            updateValues = {'order_id':(order_id),'date_updated':(currentdate)}
            db.update_query('orders', new_values,where,updateValues)
            
            response['status']  = "Success"
            response['data'] =  "Order has been updated successfully"
            return response
                
               
        except:
            response['status']  = "Failure"
            response['message'] = "Exception Error."
            return response 
      
        