import model as mod

mod_order = mod.ModelOrderClass()

class ControllerOrderClass:
    

    def get_all_orders(self,ordersCount=None):
        result = mod_order.get_all_orders(ordersCount)
        return result
    
    
    def get_order_detail(self,orderid,ordersCount=None):
        result = mod_order.get_order_detail(orderid,ordersCount)
        return result
    
        
    def order_update_status(self,data):
        result = mod_order.order_update_status(data)
        return result
    
    
    def get_all_products(self):
        
        result = mod_order.get_all_products()
        return result
    
    def add_products(self,data):
        result = mod_order.add_products(data)
        return result
    
#     def remove_order(self,orderid):
#         result = mod_order.remove_order(orderid)
#         return result
    
    def remove_item_from_order(self,orderid=None,detailid=None,data=None):
        result = mod_order.remove_item_from_order(orderid,detailid,data)
        return result
    
#     def remove_items_from_order(self,data):
#         result = mod_order.remove_items_from_order(data)
#         return result
    
    def change_item_quantity_from_order(self,detailid,newQuantity):
        result = mod_order.change_item_quantity_from_order(detailid,newQuantity)
        return result
    
    def get_messages_log(self,orderid):
        result = mod_order.get_messages_log(orderid)
        return result
    
    def send_owner_message(self,data):
        result = mod_order.send_owner_message(data)
        return result
    
    def order_update_print(self,data):
        result = mod_order.order_update_print(data)
        return result
    
    