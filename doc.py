try:
    import cvs_services
except ImportError:
    import os
    import sys
    
    # Get the absolute file path
    p = os.path.abspath(__file__)
    
    # Move 4 steps above. FIXME: This would change in case of relocation.
    for i in range(0, 2):
        p = os.path.split(p)[0]
    # Append to PYTHONPATH
    sys.path.append(p)

from cvs_services import service as srv
print(srv.categories.__doc__)
