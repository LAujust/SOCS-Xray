from .utils import *
from .fetch import *
from .search import *
from .mail import *

class Pipeline(object):
    def __init__(self,email,password,root='./main/'):
        #"EP account is essential."
        self.authorize(email,password)
        self.root = root
        self.initialize()
        
    
    def authorize(self,email,password):
        self.account = {'email':email,'password':password}  #EPSC account
        
    def initialize(self):
        if not os.path.exists(self.root):
            os.mkdir(self.root)
            print('Working on new direction. ')
        else:
            if not os.path.exists(os.path.join(self.root,'matched.yaml')):
                self.matched = dict()
                with open(os.path.join(self.root,'matched.yaml'), "w", encoding="utf-8") as f:
                    yaml.safe_dump(self.matched, f, allow_unicode=True)
                    f.close()
                print('Starting with NULL dataset. ')
            else:
                with open(os.path.join(self.root,'matched.yaml'), "r", encoding="utf-8") as f:
                    self.matched = yaml.safe_load(f)
                    f.close()
                print('Matched table loaded. ')
                
        
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

            try:
                response = requests.get(
                            api_url,
                            headers={"tdic-token": token},  
                            params={"token":token} #both hearders and params are need
                        )
                response.raise_for_status()

                data = response.json()
                obs_time.append(data['first_obs_date'])
            except:
                obs_time.append('2050-01-01T00:00:00Z')
                print('Fail on %s'%id)
        
        return obs_time
        
    def run(self):
        pass
        
    