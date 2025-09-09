from .utils import *

def update_WXT_source_list(EMAIL,PASSWORD,save_dir=None):

    print('\n\n============================================================')
    print('================= Updata WXT Source List ===================')
    print('============================================================')

    #Initialization
    url = "https://ep.bao.ac.cn/ep/api/get_tokenp"
    api_url = "https://ep.bao.ac.cn/ep/data_center/api/identified_source_list"
    save_dir = '/mnt/rdliang/SN/EPOT_match/'

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

