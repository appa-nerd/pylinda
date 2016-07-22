#!/usr/bin/python
"""
"""

# import os
# import sys
# import time
# import pickle
# import socket
# import select
# import __main__
# import datetime

"""------------------------------------------------------------*
    Declare
#------------------------------------------------------------"""

"""------------------------------------------------------------*
    Classes
    _ = Any(Any)
    _int = Any(int)
#------------------------------------------------------------"""

class Any(object):
    def __init__(self,Type):
        if type(Type) == type:
            self.my_type = Type
        else:
            self.my_type = type(Type)

    def __eq__(self,other):
        if self.my_type == Any:
            return True
        elif type(other) == self.my_type:
            return True
        else:
            return False
