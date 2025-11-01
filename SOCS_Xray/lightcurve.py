from .utils import *
import re, io
from alerce.core import Alerce
import sqlalchemy as sa


def atlas_lc(ra,dec,account:str,password:str,mjd_min=None,mjd_max=None,comment:str='SOCS_bot'):
    
    if mjd_max == None:
        mjd_max = Time.now().mjd
    if mjd_min == None:
        mjd_min = mjd_max - 30
    
    #Check Authenticity
    BASEURL = "https://fallingstar-data.com/forcedphot"
    resp = requests.post(url=f"{BASEURL}/api-token-auth/", data={'username': account, 'password': password})
    if resp.status_code == 200:
        token = resp.json()['token']
        print(f'Your token is {token}')
        headers = {'Authorization': f'Token {token}', 'Accept': 'application/json'}
    else:
        print(f'ERROR {resp.status_code}')
        print(resp.json())
        
    #Request Data
    task_url = None
    while not task_url:
        with requests.Session() as s:
            resp = s.post(f"{BASEURL}/queue/", headers=headers, data={
                'ra': ra, 'dec': dec, 'mjd_min': mjd_min,'mjd_max':mjd_max,'comment':comment})

            if resp.status_code == 201:  # successfully queued
                task_url = resp.json()['url']
                print(f'The task URL is {task_url}')
            elif resp.status_code == 429:  # throttled
                message = resp.json()["detail"]
                print(f'{resp.status_code} {message}')
                t_sec = re.findall(r'available in (\d+) seconds', message)
                t_min = re.findall(r'available in (\d+) minutes', message)
                if t_sec:
                    waittime = int(t_sec[0])
                elif t_min:
                    waittime = int(t_min[0]) * 60
                else:
                    waittime = 10
                print(f'Waiting {waittime} seconds')
                time.sleep(waittime)
            else:
                print(f'ERROR {resp.status_code}')
                print(resp.json())
                sys.exit()
                
    result_url = None
    while not result_url:
        with requests.Session() as s:
            resp = s.get(task_url, headers=headers)

            if resp.status_code == 200:  # HTTP OK
                if resp.json()['finishtimestamp']:
                    result_url = resp.json()['result_url']
                    print(f"Task is complete with results available at {result_url}")
                    break
                elif resp.json()['starttimestamp']:
                    print(f"Task is running (started at {resp.json()['starttimestamp']})")
                else:
                    print("Waiting for job to start. Checking again in 10 seconds...")
                time.sleep(10)
            else:
                print(f'ERROR {resp.status_code}')
                print(resp.json())
                sys.exit()

    with requests.Session() as s:
        textdata = s.get(result_url, headers=headers).text
    dfresult = pd.read_csv(io.StringIO(textdata.replace("###", "")), sep=r"\s+")
    
    return dfresult
        

def ztf_irsa_lc(ra, dec, band:str, match_rad:float=5, mjd_min=None, mjd_max=None):
    # FROM ISRA
    """
    :pos[str]   'ra dec' in deg
    :band[str] g/r/i
    :match_rad[float] mathing radius in arcsec
    :return: astropy.io.votable
    """
    if mjd_max == None:
        mjd_max = Time.now().mjd
    if mjd_min == None:
        mjd_min = mjd_max - 30

    match_rad = match_rad/3600
    API =  f"https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves?POS=CIRCLE%20{ra}%20{dec}%20{match_rad}&BANDNAME={band}&TIME={mjd_min} {mjd_max}"
    lcdata = parse_single_table(API).to_table()
    return lcdata

def alerce_lc(oid):
    
    alerce = Alerce()
    det = alerce.query_detections(oid=oid,format='votable')
    force = alerce.query_forced_photometry(oid=oid,format='pandas')
    return det, force