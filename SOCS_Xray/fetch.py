from .utils import *



def update_WXT_source_list(EMAIL,PASSWORD,save_dir=None):

    print('\n\n============================================================')
    print('================= Updata WXT Source List ===================')
    print('============================================================')

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

def get_TNS(filename='tns_public_objects.csv.zip',save_dir=',.'):
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
        print(f"Downloaded: {filename}")
    else:
        print(f"Failed to download {filename}. Status code: {response.status_code}")