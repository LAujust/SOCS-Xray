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
        
    def request_obs_time(self,ids):
        url = "https://ep.bao.ac.cn/ep/api/get_tokenp"
        response = requests.post(
                url,
                json={"email": self.account['email'], "password": self.account['password']},
                headers={"Content-Type": "application/json"}
            )
        response.raise_for_status()  
        token = response.json().get("token") 

        obs_time = []
        for id in ids:
            api_url = "https://ep.bao.ac.cn/ep/data_center/get_first_obs_date?source_id=%s"%id

            response = requests.get(
                        api_url,
                        headers={"tdic-token": token},  
                        params={"token":token} #both hearders and params are need
                    )
            response.raise_for_status()
            data = response.json()
            obs_time.append(data['first_obs_date'])
        
        return obs_time
        
    def run(self):
        pass
        
    