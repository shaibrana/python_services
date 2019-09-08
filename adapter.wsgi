try:
    import cvs_services
except ImportError:
    import os
    import sys
    os.chdir(os.path.dirname(__file__))
    
    # Get the absolute file path
    p = os.path.abspath(__file__)
    
    # Move 4 steps above. FIXME: This would change in case of relocation.
    for i in range(0, 2):
        p = os.path.split(p)[0]
    # Append to PYTHONPATH
    sys.path.append(p)

import bottle  
import cvs_services.service # This loads your application
from bottle.ext import memcache as mc_plugin
import memcache

application = bottle.default_app()
application.plugin = application.install(mc_plugin.Plugin())
