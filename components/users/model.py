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

import urllib
import requests
from requests.auth import HTTPBasicAuth
#import sys;
#reload(sys);
#sys.setdefaultencoding("utf8")

#import requests
#from StringIO import StringIO


from cvs_services.config import Headers
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
db = dbm.DBLayer()

class ModelUserClass:
       
    
    def user_login(self):
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
            
            what = "userid,username,first_name,last_name,email,mob_number,user_type,status,owner_uniquecode,DATE_FORMAT(date_created,'%%Y-%%m-%%d') as date_created,DATE_FORMAT(date_updated,'%%Y-%%m-%%d') as date_updated"
            result = db.get_all('users',what,where,countValues)
            
            response['status'] = "Success"
            response['data']   = result    
            return response
        
        
        except:
            response['status']  = "Failure"
            response['message'] = "Exception Error."
            return response
        
            
    def get_all_customers(self,customerCount=None):
        response  = {}
        try:
           
            athentication = base64.b64decode(Headers()['Authentication'])
            i = athentication.split(':')
            username = i[0]
            password = i[1]
            
            status = Headers()['status']
            offset = Headers()['vtOffset']
            limit = Headers()['vtLimit']
            startDate = Headers()['vtStartDate']
            endDate = Headers()['vtEndDate']
            searchKeyWord = Headers()['searchKeyWord']
            
            
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            count = db.get_count('users',where,countValues)
          
            if count ==0:  
                return response  
                response['status']  = "Failure"
                response['message'] = "Please try with valid user name and password."
                return response
            
            what="userid,user_type"
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            user_detail=db.get_all('users',what,where,countValues)
            owner_id=user_detail[0]['userId']
            user_type=user_detail[0]['userType']
            
            
            if user_type == "sys_admin":
                where = "WHERE o.user_number = c.mobile_number"
            else:
                where = "WHERE o.owner_id = %(owner_id)s and o.user_number = c.mobile_number"
                
#             if status select in search
            if status != "":
                if user_type == "sys_admin":
                    if status =="active":
                        where += "  and c.status = 'active'"
                    else:
                        where += " and c.status = 'inactive'"
                else:
                    if status =="active":
                        where += " and c.mobile_number NOT IN (select mobile_number from customer_status where userid=%(owner_id)s)"
                    else:
                        where += " and c.mobile_number IN(select mobile_number from customer_status where userid=%(owner_id)s)"
                  
#              if date select in search     
            if startDate != "" and endDate != "":
                where += " and c.date_created >= %(startDate)s AND c.date_created <= %(endDate)s"
            elif startDate != "":
                where += " and c.date_created >= %(startDate)s"
            elif endDate != "":
                where += " and c.date_created <= %(endDate)s"
            else:
                 startDate = ""
            
            if searchKeyWord != "":
                where += " and (c.first_name LIKE  %(searchKeyWord)s"
                where += " or c.last_name LIKE %(searchKeyWord)s"
                where += " or c.mobile_number LIKE %(searchKeyWord)s"
                where += " or c.email LIKE %(searchKeyWord)s )"
            
            
            if customerCount == None:
            
                offset = Headers()['vtOffset']
                limit = Headers()['vtLimit']
                
                if offset != "" and limit != "":
                    offset_limit = (int(offset) - 1)*int(limit) 
                    where += " LIMIT "+limit+" OFFSET "+str(offset_limit)+" "
                
                elif limit != "":
                    where += " LIMIT "+limit
                
                else:
                    print "send limit with offset"
            
            
            if customerCount != None:
               
               countValues = {'owner_id': (owner_id),'status':(status),'offset':(offset),'limit':(limit),'startDate':(startDate),'endDate':(endDate),'searchKeyWord':'%'+(searchKeyWord)+'%' }
               what = "Distinct(o.user_number)"
               result = db.get_all('orders o, customers c',what,where,countValues)
               
               response['status']  = "Success"
               response['data'] = len(result)
               return response
            
            else:
        
                countValues = {'owner_id': (owner_id),'status':(status),'offset':(offset),'limit':(limit),'startDate':(startDate),'endDate':(endDate),'searchKeyWord':'%'+(searchKeyWord)+'%' }
                what = "Distinct(o.user_number),c.customer_id,c.first_name, c.last_name, c.mobile_number, c.is_payment_verify, c.email, c.status"
                result = db.get_all('orders o, customers c',what,where,countValues)
          
                if user_type == "business_owner":
                  
                    where = "WHERE userid = %(owner_id)s"
                    countValues = {'owner_id': (owner_id)}
                    what = "mobile_number"
                    customer_status = db.get_all('customer_status',what,where,countValues)
         
                    for single in result: 
                        obj = single
                        mobile_number = obj['userMobileNumber']
                        block_check = 0 
                        for single1 in customer_status: 
                            obj1 = single1
                            mobile_number_block = obj1['userMobileNumber']
                            if mobile_number == mobile_number_block:
                                obj["status"] = "inactive"
                                block_check = 1
                        if block_check == 0:
                                obj["status"] = "active"
                            
                response['status'] = "Success"
                response['data']   = result    
                return response
        
        except:
            response['status']  = "Failure"
            response['message'] = "Exception Error."
            return response
 
 
  
    def update_customer_status(self,data):
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
            
            what="userid,owner_uniquecode,user_type"
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            user_detail=db.get_all('users',what,where,countValues)
            owner_id=user_detail[0]['userId']
            owner_uniquecode = user_detail[0]['businessCode']
            user_type=user_detail[0]['userType']
           
            now  = datetime.datetime.now()
            currentdate = now.strftime("%Y-%m-%d %H:%M:%S")
            
            try:
                customer_id = data['customerId']
                status = data['status']
            except:
                response['status']  = "Failure"
                response['message'] = "Please try Again with valid post fields."
                return response
            
            
                
            where = "WHERE customer_id = %(customer_id)s"
            countValues = {'customer_id': (customer_id)}
            count = db.get_count('customers',where,countValues)
           
            if count ==0:  
                response['status']  = "Failure"
                response['message'] = "Please try with valid customerID"
                return response
           
            if status == "active" or status == "inactive":
                print "valid customer status"
            else:
                response['status']  = "Failure"
                response['message'] = "Please try with valid status"
                return response
           
            what = "mobile_number"
            result = db.get_all('customers',what,where,countValues)
            userMobileNumber = result[0]['userMobileNumber'] 
            if user_type == "sys_admin":
                where = "WHERE customer_id = %(customer_id)s"
                new_values = "date_updated = %(date_updated)s,status = %(status)s"
                updateValues = {'date_updated':(currentdate),'status':(status),'customer_id': customer_id}
                db.update_query('customers', new_values,where,updateValues)
            else:
                if status == "inactive":
                    column = ['mobile_number','userid','date_created']
                    value = [userMobileNumber,owner_id,currentdate]
                    result = db.insert_query('customer_status',column,value)
                else:
                     where = "WHERE mobile_number = %(mobile_number)s and userid = %(owner_id)s"
                     updateValues = {'mobile_number':(userMobileNumber),'owner_id':(owner_id)}
                     db.delete_query('customer_status',where,updateValues)
            
            
            if user_type == "sys_admin":
                system_name = "customer_status_by_admin"
            else:
                system_name = "customer_status_by_owner"
                    
            
            
            message_detail = self.custom_message(system_name)
            message = message_detail[0]['messageText']
            
            if user_type == "business_owner":
                what="business_name"
                where = "WHERE userid = %(owner_id)s"
                countValues = {'owner_id': (owner_id)}
                user_detail=db.get_all('users',what,where,countValues)
                businessName=user_detail[0]['businessName']
                message = message.replace("%business_name%",businessName)
            
            message = message.replace("%status%",status)
            msg_to = userMobileNumber
            
            data = {}
            data['message']=message;
            data['message_id']=message_detail[0]['defaultMessageId']
            data['message_type'] = message_detail[0]['messageType']
            data['table_name'] = "custom_default_messages";
            data['owner_id']=owner_id
            data['msg_to']=msg_to
            data['status']="sent"
            data['order_type']="customer"
            
            result = db.create_log(data)
            if result == "Failure":
                print "sms log not created"
            
            
            msg_from = "+16193910014"
            try:
                db.sms_send(msg_to, msg_from, message)
            except:
                print "sms not sent to customer"
                
            response['status'] = "Success"
            response['data']   = "Status has been updated Successfully"    
            return response
            
                
        except:
            response['status']  = "Failure"
            response['message'] = "Exception Error."
            return response

         
    def get_customer_orders(self,customerId,customerCount=None):
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
            
            offset = Headers()['vtOffset']
            limit = Headers()['vtLimit']
         
            
            what="userid,user_type"
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            user_detail=db.get_all('users',what,where,countValues)
            owner_id=user_detail[0]['userId']
            user_type=user_detail[0]['userType']
            
            where = "WHERE customers.customer_id = %(customer_id)s and orders.status!='pending' and orders.status!='system_error' AND orders.user_number=customers.mobile_number"
            what = "business_name,order_id,user_number,owner_number,owner_id,DATE_FORMAT(orders.date_begin,'%%Y-%%m-%%d %%H:%%i:%%s') as date_created,orders.status,DATE_FORMAT(orders.date_updated,'%%Y-%%m-%%d %%H:%%i:%%s') as date_updated,delivery_address,customers.first_name,customers.last_name"
           
            if user_type == "sys_admin":
               where += " and orders.owner_id = users.userid"
            else:
                where += " and orders.owner_id = %(owner_id)s and orders.owner_id = users.userid"
           
            if customerCount == None:
            
                offset = Headers()['vtOffset']
                limit = Headers()['vtLimit']
                
                if offset != "" and limit != "":
                    offset_limit = (int(offset) - 1)*int(limit) 
                    where += " LIMIT "+limit+" OFFSET "+str(offset_limit)+" "
                
                elif limit != "":
                    where += " LIMIT "+limit
                
                else:
                    print "send limit with offset"
            
            countValues = {'owner_id': (owner_id),'customer_id': (customerId),'offset':(offset),'limit':(limit)}
            if customerCount != None:
                result = db.get_all('orders,customers,users',"order_id",where,countValues)
                response['status'] = "Success"
                response['data']   = len(result)    
                return response
        
            else:
                result = db.get_all('orders,customers,users',what,where,countValues)
                response['status'] = "Success"
                response['data']   = result    
                return response
        
        except:
            response['status']  = "Failure"
            response['message'] = "Exception Error."
            return response

    def get_customer_orders_count(self,customerId):
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
            
            what="userid,user_type"
            where = "WHERE username = %(username)s AND password = %(password)s AND status = 'Active'"
            countValues = {'username': (username), 'password': (password)}
            user_detail=db.get_all('users',what,where,countValues)
            owner_id=user_detail[0]['userId']
            user_type=user_detail[0]['userType']
            
            where = "WHERE customers.customer_id = %(customer_id)s and orders.status!='pending' and orders.status!='system_error' AND orders.user_number=customers.mobile_number"
            what = "order_id"
           
            if user_type == "sys_admin":
               where += " and orders.owner_id = users.userid"
            else:
                where += " and orders.owner_id = %(owner_id)s and orders.owner_id = users.userid"
                  
            countValues = {'owner_id': (owner_id),'customer_id': (customerId)}
            result = db.get_all('orders,customers,users',what,where,countValues)
           
            response['status'] = "Success"
            response['data']   = len(result)    
            return response
        
        except:
            response['status']  = "Failure"
            response['message'] = "Exception Error."
            return response
        
    
    
    def custom_message(self,system_name):
        what="*"
        where = "WHERE system_name = %(system_name)s"
        countValues = {'system_name': (system_name)}
        result=db.get_all('custom_default_messages',what,where,countValues)
        return result
    
    def get_owner_info(self,owner_id):
        what="sms_charges,sms_rate"
        where = "WHERE userid = %(owner_id)s"
        countValues = {'owner_id': (owner_id)}
        result=db.get_all('user_rules',what,where,countValues)
        return result

    def sms_log(self,data):
        response = {}
        result = db.create_log(data)
        if result == "Success":
            response['status'] = "Success"
            response['data']   = "Sms Log inserted Successfully"    
            return response
       
        response['status']  = "Failure"
        response['message'] = "Exception Error."
        return response
