from .utils import *
from .fetch import *
from .search import *
from .mail import *

class Pipeline(object):
    def __init__(self,email,password):
        #"EP account is essential."
        self.authorize(email,password)
    
    def authorize(self,email,password):
        self.account = {'email':email,'password':password}  #EPSC account
        
    