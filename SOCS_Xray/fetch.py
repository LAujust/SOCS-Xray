from .utils import *
from alerce.core import Alerce
import sqlalchemy as sa
from lasair import LasairError, lasair_client as lasair
import json



def update_WXT_source_list(EMAIL,PASSWORD,save_dir=None):

    #Initialization
    url = "https://ep.bao.ac.cn/ep/api/get_tokenp"
    api_url = "https://ep.bao.ac.cn/ep/data_center/api/identified_source_list"

    response = requests.post(
                url,
                json={"email": EMAIL, "password": PASSWORD},
                headers={"Content-Type": "application/json"}
            )
    response.raise_for_status()  
    token = response.json().get("token") 
    # print(token) # the token will never expire
    response = requests.get(
                api_url,
                headers={"tdic-token": token},  
                params={"token":token} #both hearders and params are need
            )
    response.raise_for_status()

    data = response.json()

    df = pd.DataFrame(data)
    table = Table.from_pandas(df)
    for col in table.colnames:  #convert list elements to string
        if any(isinstance(val, list) for val in table[col]):
            table[col] = [str(val) for val in table[col]]
            
            
    #==== Add Stellar Flare List ===
    api_url = "https://ep.bao.ac.cn/ep/data_center/api/stellar_flare_list"
    #######
    response = requests.post(
                url,
                json={"email": EMAIL, "password": PASSWORD},
                headers={"Content-Type": "application/json"}
            )
    response.raise_for_status()  
    token = response.json().get("token") 
    # print(token) # the token will never expire

    response = requests.get(
                api_url,
                headers={"tdic-token": token},  
                params={"token":token} #both hearders and params are need
            )
    response.raise_for_status()

    #data = response.json()
    data = response.json()['sources']
    df = pd.DataFrame(data)
    table_star = Table.from_pandas(df)
    for col in table_star.colnames:  #convert list elements to string
        if any(isinstance(val, list) for val in table_star[col]):
            table_star[col] = [str(val) for val in table_star[col]]
            
    for colname in table.colnames:
        table_star[colname] = table_star[colname].astype(table[colname].dtype)
        
    table = vstack((table,table_star))

    if save_dir:
        table.write(os.path.join(save_dir,'EP_identified_source_list.csv'),format='csv',overwrite=True)
    print("%s has been UPDATED at %s"%('EP_identified_source_list.csv',Time.now()))

    return table

def get_TNS(filename='tns_public_objects.csv.zip',save_dir='./'):
    
    API_KEY = '48aa6e2dfcb5893b987dda29b3f3938e97e8db43'
    BOT_ID = '164028'
    BOT_NAME = 'bot_BC'

    # API_KEY = '1745589895680b9687d5d2a9.98026628'
    # BOT_ID = '197764'
    # BOT_NAME = 'EP_bot_lrd'

    # The base URL for the TNS public objects CSV files
    BASE_URL = "https://www.wis-tns.org/system/files/tns_public_objects/"
    """Helper function to download a file from a given URL."""
    headers = {
        'user-agent': f'tns_marker{{"tns_id":{BOT_ID},"type":"bot","name":"{BOT_NAME}"}}',
    }
    data = {'api_key': API_KEY}
    
    url = BASE_URL + filename
    response = requests.post(url, headers=headers, data=data, stream=True)

    if response.status_code == 200:
        with open(os.path.join(save_dir,filename), 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
    else:
        print(f"Failed to download {filename}. Status code: {response.status_code}")
        
    #Unzip
    os.chdir(save_dir)
    unzip_command = f'unzip -o {filename}'
    subprocess.run(unzip_command, shell=True)
    base_filename = filename[:-4]  # 去除.zip后缀
    os.remove(os.path.join(save_dir,filename))

    tns_table = Table.read(os.path.join(save_dir,base_filename),format='csv',header_start=1, data_start=2)
    tns_table.write(os.path.join(save_dir,base_filename),format='csv',overwrite=True)
    return tns_table
    


def get_Alerce(query):

    url = "https://raw.githubusercontent.com/alercebroker/usecases/master/alercereaduser_v4.json"
    params = requests.get(url).json()['params']
    engine = sa.create_engine(f"postgresql+psycopg2://{params['user']}:{params['password']}@{params['host']}/{params['dbname']}")
    engine.begin()
    alerce_table = pd.read_sql_query(query, con=engine)
    alerce_table = Table.from_pandas(alerce_table)
    return alerce_table


def get_Lasair(ndays):
    
    sys.path.append('API_ztf')
    endpoint = "https://lasair-ztf.lsst.ac.uk/api"
    API_TOKEN = 'cc411e15090ab35754f0d3673ddb4ceb671ee8cf'
    L = lasair(API_TOKEN, endpoint=endpoint)
    
    rows = L.query("""objects.objectId,
        objects.ramean,
        objects.decmean,
        objects.jdmin - 2400000.5 AS mjdmin,
        objects.jdmax - 2400000.5 AS mjdmax,
        objects.magrmin,
        objects.ncandgp AS ndet,
        objects.rmag,
        sherlock_classifications.classification AS classification""",
            """objects,
                sherlock_classifications,
                watchlist_hits,
                crossmatch_tns""",
            """objects.objectId = sherlock_classifications.objectId
                AND objects.objectId = watchlist_hits.objectId
                AND objects.jdmin > jdnow() - %s
                AND NOT (
                    objects.distpsnr1 < 2
                    AND objects.sgscore1 > 0.49
                )
                AND classification in ("SN","NT","ORPHAN")
                """%(ndays),
                limit=1e4)

    lasair_table = Table(rows)
    lasair_table[lasair_table['ndet']==None] = 2
    lasair_table['ndet'] = lasair_table['ndet'].astype(np.int64)
    
    return lasair_table




def request_obs_time(EMAIL,PASSWORD,ids):
    EMAIL = "liangrd@bao.ac.cn" # your login email in EP TDAIC
    PASSWORD = "Liang981127"
    url = "https://ep.bao.ac.cn/ep/api/get_tokenp"
    response = requests.post(
            url,
            json={"email": EMAIL, "password": PASSWORD},
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


def base_alerce_query(ndet,mjdfirst,types=["SN", "AGN"],classifier='stamp_classifier'):
    if ndet == 1:
        ndet = '<2'
    else:
        ndet = '>%s'%(ndet-1)
        
    query = '''
        SELECT
            object.oid, object.meanra, object.meandec, object.firstmjd,
            object.ndet, object.stellar, probability.probability, 
            probability.classifier_name, probability.classifier_version,
            probability.class_name
        FROM 
            object 
        INNER JOIN
            probability
        ON 
            object.oid = probability.oid
        WHERE
            object.firstMJD > %s
            AND probability.classifier_name = '%s'
            AND probability.class_name IN (%s)
            AND probability.ranking=1
            AND probability.probability>0.3
            AND object.ndet %s
        '''% (mjdfirst,classifier, ",".join([f"'{i}'" for i in types]),ndet)
        
    return query