import MySQLdb as mdb
import sys 
from cvs_services.config import Connections, Headers
from cvs_services.decorators import transform_for_rest
import bottle
import base64
import datetime
import string

bottle.debug(True)
bottle.TEMPLATES.clear()


class DBLayer: 
    
    field_map = {
                
                'userid' : 'userId',
                'username': 'userName',
                'first_name' : 'firstName',
                'last_name':'lastName',
                'email': 'email',
                'mob_number':'MobileNumber',
                'user_type':'userType',
                'status': 'status',
                'owner_uniquecode': 'businessCode',
                'date_created':'dateCreated',
                'date_updated': 'dateUpdated',
                'order_id': 'orderId',
                'user_number': 'userMobileNumber',
                'owner_number': 'ownerMobileNumber',
                'delivery_address': 'deliveryAddress',
                'order_detail_id': 'orderDetailId',
                'product_id': 'productId',
                'base_price': 'productBasePrice',
                'quantity': 'quantity',
                'product_name': 'productName',
                'category_id': 'categoryId',
                'product_base_price': 'productBasePrice',
                'customer_token': 'customerToken',
                'default_paymethod_token': 'defaultPaymethodToken',
                'add_product_transaction_id':'addProductTransactionId',
                'change_quantity_transaction_id':'changeQuantityTransactionId',
                'owner_id':'ownerId',
                'tax_rate':'taxRate',
                'query':'Message',
                'amount':'amount',
                'delivery_charge':'deliveryCharge',
                'convenience_charge_customer':'convenienceChargeCustomer',
                'customer_id':"customerId",
                'city':'city',
                'state':'state',
                'zip':'zip',
                'mobile_number': 'userMobileNumber',
                'total_amount': 'totalAmount',
                'auth_key': 'authenticationKey',
                'business_name':'businessName',
                'is_print':'isPrint',
                'date_begin':'dateBegin',
                'default_message_id':'defaultMessageId',
                'system_name':'systemName',
                'message_text':'messageText',
                'message_type':'messageType',
                'menu_type':'menuType',
                "sms_charges":"smsCharges",
                "sms_rate":"smsRate",
                "totalProducts":"totalProducts",
                "totalQuantity":"totalQuantity",
                "product_tax":"productTax",
                "settlement_id":"settlementId",
                "delivery_time":"deliveryTime",
                "pickup_time":"pickupTime",
                "max_amount":"maxAmount",
                "amount_per_day":"amountPerDay",
                "min_amount":"minAmount"
                
                }
    
    def __init__(self):
            pass   
          
    def get_count(self, table, where=None,values=None,field=""):
        """ return the number of rows found in db given table, what, where"""
        
        try:
            conn = Connections()['mysqldbconnection']                  
            cur = conn.cursor(mdb.cursors.DictCursor)
            
            if field=="":
                query="SELECT count(*) as cnt FROM %s %s" % (table, where)
            
            else:
                query="SELECT count(Distinct %s) as cnt FROM %s %s" % (field,table, where)
            
            print query
            
            cur.execute(query,values)        
            data = cur.fetchall()
             
            return data[0]['cnt']
        
        except mdb.Error, e: 
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit(1)    
        
        finally:            
            pass
      
    def row_count(self, table, where=None):
        """ return the number of rows found in db given table, what, where"""
        try:
            conn = Connections()['mysqldbconnection']                    
            cur = conn.cursor(mdb.cursors.DictCursor)
            query="SELECT count(*) as total FROM %s %s" % (table, where)
            print query
            cur.execute(query,value)            
            if not cur.rowcount:
                return 0
            else:           
                return 1 
            
        except mdb.Error, e: 
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit(1)    
        finally:            
            pass
        
    @transform_for_rest
    def get_all(self, table, what, where=None, values=None, limit = False, groupby="", order= True): 
        
        try:           
            conn = Connections()['mysqldbconnection']                  
            cur = conn.cursor(mdb.cursors.DictCursor)   
            
            query = """SELECT %s FROM %s %s """ % (what, table, where) 
            
            if order:
                query = query + Headers()['By'] + " "
            if limit:
                query = query + Headers()['Limit']
            
            print query
            print values
            cur.execute(query,values)
            data = cur.fetchall() 
        
            return data
        
        except mdb.Error, e: 
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit(1)    
        finally:            
            pass
        
    @transform_for_rest    
    def generic_query(self,query, values=None):
        
        try:
            conn = Connections()['mysqldbconnection']                  
            cur = conn.cursor(mdb.cursors.DictCursor)
            
            print query
            
            cur.execute(query,(values))
            conn.commit()
            data = cur.fetchall()
            
            return data
        
        except mdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit(1)  
        
        finally:
            pass
    
    def insert_query(self,table, column, values):
        try:
            conn = Connections()['mysqldbconnection']                  
            cur = conn.cursor(mdb.cursors.DictCursor)
            #query = "INSERT INTO %s %s Values %s" % (table,column,values)
            query = "INSERT INTO " + table + " ("
            for col in column:
                query += col + ","
            
            
            query = query[:-1]
            
            query += ") VALUES ( "
            
            for index in column:
                query += "%s" + ","
            
            query = query[:-1]
            query += ") "
            
            print query
            conn = Connections()['mysqldbconnection']                  
            cur = conn.cursor(mdb.cursors.DictCursor)
            cur.execute(query,values)
            
            db_id = conn.insert_id()

            conn.commit()
            data={}
            data['id'] = db_id
            return data
        
        except mdb.Error, e: 
            print e.args
            sys.exit(1)    
        
        finally:            
            pass    
        
        
    def update_query(self, table, values, where, updateValues=None):
        try:
            
            conn = Connections()['mysqldbconnection']                  
            cur = conn.cursor(mdb.cursors.DictCursor)
            query = "UPDATE %s SET %s %s" % (table, values, where) 
            
            print query
            
            print "values command"
            print values
            print "where command"
            print where
            print "updated command"
            print updateValues
            cur.execute(query,updateValues)
            conn.commit()
        
        except mdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit(1)    
        
        finally:            
            pass
        
    def delete_query(self, table, where, values=None):
        try:
            
            conn = Connections()['mysqldbconnection']                  
            cur = conn.cursor(mdb.cursors.DictCursor)
            query = "Delete From %s %s" % (table, where) 
            
            print query
            
            cur.execute(query,values)
            conn.commit()
        
        except mdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit(1)    
        
        finally:            
            pass
        
    
    @transform_for_rest
    def auth_key(self): 
        try:           
            conn = Connections()['mysqldbconnection']                  
            cur = conn.cursor(mdb.cursors.DictCursor)   
            
            key = Headers()['Key']
            athentication = base64.b64decode(Headers()['Authentication'])
            i = athentication.split(':')
            username = i[0]
            password = i[1]
        
            where = "WHERE username = %(username)s AND password = %(password)s AND auth_key = %(key)s AND status = 'Active'"
            values = {'username': (username), 'password': (password), 'key': (key)}
            query = """SELECT %s FROM %s %s """ % ("*", "users", where) 
            
            print query
            print values
            cur.execute(query,values)
            data = cur.fetchall() 
        
            return data
        
        except mdb.Error, e: 
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit(1)    
        finally:            
            pass    
    def create_database(self, dbname, dbuser, dbpass):
        db = mdb.connect(host="localhost",user="root",passwd="53cr3t")
        cursor = db.cursor()
        cursor.execute("CREATE DATABASE %s" % (dbname))
        cursor.execute("GRANT USAGE ON *.* TO %s@localhost IDENTIFIED BY '%s'" % (dbuser, dbpass))
        cursor.execute("GRANT ALL PRIVILEGES ON %s.* TO %s@localhost" % (dbname, dbuser))   
        


    def create_log(self,message_detail):
        try:
            status =  message_detail['status']
            order_type =  message_detail['order_type']
            msg_to = message_detail['msg_to']  
            message_type = message_detail['message_type']        
            try:
                order_id = message_detail['order_id']
                if order_id == "":
                    order_id = None 
            except:
                order_id = None
            
            try:
                owner_id = message_detail['owner_id']
            except:
                owner_id = None
           
            now  = datetime.datetime.now()
            currentdate = now.strftime("%Y-%m-%d %H:%M:%S")
          
            if  status=="sent":
                message_body = message_detail['message']
            else:
                message_body = message_detail['message_received']
        
#       check total number to sms  
            total_sms = float(len(message_body))/160;
            i = str(total_sms).split('.')
            total_sms = i[0]
            if len(i)==2:
                total_sms = int(total_sms) + 1
           
    #        by default per sms charges if owner set default charges
            per_sms_charges = "0.0075"
            sms_cost = 0.00
    
    #         if owner id exist get sms changes
            if  owner_id:
                owner_id = message_detail['owner_id']
                
                what="sms_charges,sms_rate"
                where = "WHERE userid = %(owner_id)s"
                countValues = {'owner_id': (owner_id)}
                owner_detail=self.get_all('user_rules',what,where,countValues)
           
                sms_charges = owner_detail[0]['smsCharges']
                sms_rate = owner_detail[0]['smsRate']
                
                if sms_charges == "1":
                    sms_cost = float(total_sms) * float(sms_rate)
                else: 
                    sms_cost = float(total_sms) * float(per_sms_charges)
                    
            else:
                sms_cost = float(total_sms) * float(per_sms_charges)
          
            if status == "sent":
                
                sent_message = message_detail['message']
                message_id = message_detail['message_id']        
                table_name = message_detail['table_name']        
            
                column = ['status','user_number','order_id','table_name','custom_message_id','custom_message_name','sent_body','cost','order_type','date_created']
                value = [status,msg_to,order_id,table_name,message_id,message_type,sent_message,sms_cost,order_type,currentdate]
                result = self.insert_query('order_log',column,value)
            
            else:
                
                message_received = message_detail['message_received']
                message_sid = message_detail['message_sid']        
             
                column = ['status','user_number','order_id','received_body','message_sid','cost','order_type','date_created']
                value = [status,msg_to,order_id,message_received,message_sid,sms_cost,order_type,currentdate]
                result = self.insert_query('order_log',column,value)
               
                return "Success"
            
                
        except:
            return "Failure"
    
    
    def sms_send(self,msg_to,msg_from,message):
        import twilio
        import twilio.rest
        from twilio.rest import TwilioRestClient
        
        # Your Account Sid and Auth Token from twilio.com/user/account
        account_sid = "ACb96b79198137f79f0fd78cc195bc42d0"
        auth_token  = "9e1b9f25c3aa12130a5e75ecda5b503e"
        client = twilio.rest.TwilioRestClient(account_sid, auth_token)
         
        result = client.messages.create(
            body = message,
            to = msg_to,    # Replace with your phone number
            from_= msg_from) # Replace with your Twilio number

       