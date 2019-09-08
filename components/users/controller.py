import model as mod

mod_user = mod.ModelUserClass()

class ControllerUserClass:
    

    #use the decorator here which uses dictionary and also declare dictionary here    
  
    
    def user_login(self):
        result = mod_user.user_login()
        return result
        
    def get_all_customers(self,customerCount=None):
        result = mod_user.get_all_customers(customerCount)
        return result
    
    
    def update_customer_status(self,data):
        result = mod_user.update_customer_status(data)
        return result
   
    def get_customer_orders(self,customerId,customerCount=None):
        result = mod_user.get_customer_orders(customerId,customerCount)
        return result
    
    def sms_log(self,data):
        result = mod_user.sms_log(data)
        return result
   
    