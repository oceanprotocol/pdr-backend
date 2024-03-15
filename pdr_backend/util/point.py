from collections import OrderedDict

from enforce_typing import enforce_types

class Point(OrderedDict):
    
    @enforce_types
    def __str__(self):
        s = "{"
        s += ", ".join([f"{key}={val}" for key, val in self.items()])
        s += "}"
        return s
        
