#"decorators"
    
def fieldmapping(results, field_map):
        result = []
        for result_iter in results:
            resmap = {}        
            if result_iter.has_key('timestamp'):
                result_iter['timestamp'] = result_iter['timestamp'].strftime("%d/%m/%y %H:%M")            
            for k in field_map:
                if result_iter.has_key(k):                              
                    resmap[field_map[k]] = result_iter[k]
            result.append(resmap)
        return result
    
def transform_for_rest(f):
    """ Decorators 
    this decorator changes the result set keys to the keys that are to be returned in the rest api response
    for example username is changed to userName
    """
    #def decorator(self, vars=None, what="*", where=None, order=None, group=None, limit=None, offset=None, values=None):
    def decorator(self, *args, **kwargs):
        #results = f(self, vars, what=what, where=where, order=order, group=group, limit=limit, offset=offset)
        results = f(self, *args, **kwargs)
        changed_result = [] 
        if len(results) > 0:
            changed_result = fieldmapping(results, self.field_map)            
        return changed_result            
    return decorator



