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
        self.tnow = Time.now()
        
    
    def authorize(self,email,password):
        self.account = {'email':email,'password':password}  #EPSC account
        
    def initialize(self):
        """
        [matched] stores all candidates passed your filters. The unique id is pair of X-ray name and optical name tuple, i.e. (EP240506a, AT2024ofs), (A85_1, SN 025ujd)
        """
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
    
    def update_TNS(self,replace=False):
        if os.path.exists(os.path.join(self.root,'tns_public_objects_old.csv')):   
            old = Table.read(os.path.join(self.root,'tns_public_objects_old.csv'),format='csv')
            new = get_TNS(save_dir=self.root)
            self.TNS_table = setdiff(new,old,keys=["name_prefix","name"])
        else:
            self.TNS_table = get_TNS(save_dir=self.root)[:200]
            new = self.TNS_table
            
        if replace:
            new.write(os.path.join(self.root,'tns_public_objects_old.csv'),format='csv',overwrite=True)
            
        tns_name = [self.TNS_table['name_prefix'][i]+self.TNS_table['name'][i] for i in range(len(self.TNS_table))]
        self.TNS_table['tns_name'] = tns_name
        self.TNS_table['firstmjd'] = Time(self.TNS_table['discoverydate']).mjd
        self.TNS_table['link'] = ['https://www.wis-tns.org/object/'+self.TNS_table['name'][i] for i in range(len(self.TNS_table))]
        
        self.TNS_table.rename_columns(['ra','declination','tns_name'],['o_ra','o_dec','oid'])
        self.TNS_table = self.TNS_table['oid','o_ra','o_dec','firstmjd','link']
        
    def update_ZTF(self,ndays=10):
        firstmjd_2 = self.tnow.mjd - ndays #at least 2 det
        firstmjd_1 = self.tnow.mjd - 2 #only 1 det
        
        lasair_table = alerce_table = None
        
        try:
            lasair_table = get_Lasair(ndays)
        except Exception as e:
            print('Fail on Lasair: %s'%e)
        
        try:
            alerce_table_2 = get_Alerce(base_alerce_query(2,firstmjd_2))
            alerce_table_1 = get_Alerce(base_alerce_query(1,firstmjd_1))
            alerce_table = vstack((alerce_table_2,alerce_table_1))
        except Exception as e:
            print('Fail on Alerce: %s'%e)
            
        if alerce_table is None and lasair_table is not None:
            ZTF_clean = lasair_table['objectId','ramean','decmean','mjdmin','ndet','classification']
            ZTF_clean.rename_columns(['objectId','ramean','decmean','mjdmin','classification'],
                                    ['oid','ztf_ra','ztf_dec','firstmjd','class'])
        elif alerce_table is not None and lasair_table is None:
            ZTF_clean = alerce_table['oid','meanra','meandec','probability','firstmjd','ndet','class_name']
            ZTF_clean.rename_columns(['meanra','meandec','class_name'],['ztf_ra','ztf_dec','class'])
        elif alerce_table is None and lasair_table is None:
            raise KeyError('Fail on Alerce and Lasair')
        else: #Both Lasair and Alerce works
            c_alerce = SkyCoord(alerce_table['meanra'],alerce_table['meandec'],unit=u.deg)
            c_lasair = SkyCoord(lasair_table['ramean'],lasair_table['decmean'],unit=u.deg)

            source_matched_idx, cat_matched_idx, cat_matched_sep = match_cat(c_alerce,c_lasair,radius=5*u.arcsec,seperation=True)

            Alerce_clean = alerce_table[~source_matched_idx]
            Lasair_clean = lasair_table

            Alerce_clean = Alerce_clean['oid','meanra','meandec','probability','firstmjd','ndet','class_name']
            Lasair_clean = Lasair_clean['objectId','ramean','decmean','mjdmin','ndet','classification']
            Lasair_clean['link'] = ['https://lasair-ztf.lsst.ac.uk/objects/%s'%id for id in Lasair_clean['objectId']]
            Alerce_clean['link'] = ['https://alerce.online/object/%s'%id for id in Alerce_clean['oid']]
            Lasair_clean['probability'] = [1.] * len(Lasair_clean)
            Lasair_clean['pipeline'] = ['Lasair'] * len(Lasair_clean)
            Alerce_clean['pipeline'] = ['Alerce'] * len(Alerce_clean)

            Alerce_clean.rename_columns(['meanra','meandec','class_name'],['o_ra','o_dec','class'])
            Lasair_clean.rename_columns(['objectId','ramean','decmean','mjdmin','classification'],
                                        ['oid','o_ra','o_dec','firstmjd','class'])

            #Combine to ONE table
            ZTF_clean = vstack((Alerce_clean,Lasair_clean))

        #Save
        print(' ZTF daily alert searching done! ')
        ZTF_clean_unique = unique(ZTF_clean,keys='oid')
        self.ZTF_clean = ZTF_clean_unique['oid','o_ra','o_dec','firstmjd','link']
        
        
        
    def run(self,ndays=10):
        pass
        
    