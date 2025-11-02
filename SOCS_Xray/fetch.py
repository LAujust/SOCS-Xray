from .utils import *
from alerce.core import Alerce
import sqlalchemy as sa
from lasair import LasairError, lasair_client as lasair
import json
import time
import datetime
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout



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
    response = requests.post(url, headers=headers, data=data, timeout=180, stream=True)

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


def search_TNS(user_id,user_name,url_parameters={"discovered_period_value" : "10", "discovered_period_units" : "days", 
                        "format" : "csv", "num_page" : "200",},save_dir='./'):
    TNS                  = "www.wis-tns.org"
    url_tns_search       = "https://" + TNS + "/search"
    TNS_UID              = user_id
    TNS_USER_NAME        = user_name
    USER_OR_BOT          = "user"
    MERGE_TO_SINGLE_FILE  = 1

    ext_http_errors       = [403, 500, 503]
    err_msg               = ["Forbidden", "Internal Server Error: Something is broken", "Service Unavailable"]

    #----------------------------------------------------------------------------------

    def set_user_tns_marker():
        tns_marker = 'tns_marker{"tns_id": "' + str(TNS_UID) + '", "type": "user", "name": "' + TNS_USER_NAME + '"}'
        return tns_marker

    def is_string_json(string):
        try:
            json_object = json.loads(string)
        except Exception:
            return False
        return json_object

    def response_status(response):
        json_string = is_string_json(response.text)
        if json_string != False:
            status = "[ " + str(json_string['id_code']) + " - '" + json_string['id_message'] + "' ]"
        else:
            status_code = response.status_code
            if status_code == 200:
                status_msg = 'OK'
            elif status_code in ext_http_errors:
                status_msg = err_msg[ext_http_errors.index(status_code)]
            else:
                status_msg = 'Undocumented error'
            status = "[ " + str(status_code) + " - '" + status_msg + "' ]"
        return status

    def print_response(response, page_num):
        status = response_status(response)
        if response.status_code == 200:     
            stats = 'Page number ' + str(page_num) + ' | return code: ' + status + \
                    ' | Total Rate-Limit: ' + str(response.headers.get('x-rate-limit-limit')) + \
                    ' | Remaining: ' + str(response.headers.get('x-rate-limit-remaining')) + \
                    ' | Reset: ' + str(response.headers.get('x-rate-limit-reset') + ' sec')
        
        else:       
            stats = 'Page number ' + str(page_num) + ' | return code: ' + status        
        print (stats)

    def get_reset_time(response):
        # If any of the '...-remaining' values is zero, return the reset time
        for name in response.headers:
            value = response.headers.get(name)
            if name.endswith('-remaining') and value == '0':
                return int(response.headers.get(name.replace('remaining', 'reset')))
        return None        

    # function for searching TNS with specified url parameters
    def search_tns():
        #--------------------------------------------------------------------
        # extract keywords and values from url parameters
        keywords = list(url_parameters.keys())
        values = list(url_parameters.values())
        #--------------------------------------------------------------------
        # flag for checking if url is with correct keywords
        wrong_url = False
        # check if keywords are correct
        for i in range(len(keywords)):
            if keywords[i] not in URL_PARAMETERS:
                print ("Unknown url keyword '"+keywords[i]+"'\n")
                wrong_url = True
        # check flag
        if wrong_url == True:
            print ("TNS search url is not in the correct format.\n")
        #--------------------------------------------------------------------
        # else, if everything is correct
        else:
            # current date and time
            current_datetime = datetime.datetime.now()
            current_date_time = current_datetime.strftime("%Y%m%d_%H%M%S")
            # current working directory
            cwd = save_dir       
            # create searched results folder
            if MERGE_TO_SINGLE_FILE == 0:
                tns_search_folder = "tns_search_data_" + current_date_time
                tns_search_folder_path = os.path.join(cwd, tns_search_folder)
                os.mkdir(tns_search_folder_path)
                print ("TNS searched data folder /" + tns_search_folder + "/ is successfully created.\n")            
            # file containing searched data
            if "format" in keywords:
                extension = "." + url_parameters["format"]
            else:
                extension = ".txt"
            tns_search_file = "tns_search_data" + extension
            tns_search_file_path = os.path.join(cwd, tns_search_file)
            #--------------------------------------------------------------------
            # build TNS search url
            url_par = ['&' + x + '=' + y for x, y in zip(keywords, values)]
            tns_search_url = url_tns_search + '?' + "".join(url_par)
            #--------------------------------------------------------------------
            # page number
            page_num = 0
            # searched data
            searched_data = []
            # go trough every page
            while True:
                # url for download
                url = tns_search_url + "&page=" + str(page_num)
                # TNS marker !!!only user!!!
                tns_marker = set_user_tns_marker()
                # headers
                headers = {'User-Agent': tns_marker}
                # downloading file using request module
                response = requests.post(url, headers=headers, stream=True)
                # chek if response status code is not 200, or if returned data is empty
                if (response.status_code != 200) or (len((response.text).splitlines()) <= 1):
                    if response.status_code != 200:
                        print ("Sending download search request for page num " + str(page_num + 1) + "...")
                        print_response(response, page_num + 1)
                    break            
                print ("Sending download search request for page num " + str(page_num + 1) + "...")
                # print status code of the response
                print_response(response, page_num + 1)
                # get data
                data = (response.text).splitlines()
                # create file per page
                if MERGE_TO_SINGLE_FILE == 0:
                    tns_search_f = "tns_search_data_" + current_date_time + "_part_" + str(page_num + 1) + extension
                    tns_search_f_path = os.path.join(tns_search_folder_path, tns_search_f)
                    f = open(tns_search_f_path, 'w')
                    for el in data:
                        f.write(el + '\n')
                    f.close() 
                    if len(data) > 2:
                        print ("File '" + tns_search_f + "' (containing " + str(len(data) - 1) + " rows) is successfully created.\n")                     
                    else: 
                        print ("File '" + tns_search_f + "' (containing 1 row) is successfully created.\n")
                else:
                    print ("")
                # add to searched data
                if page_num == 0:
                    searched_data.append(data)
                else:
                    searched_data.append(data[1 : ])
                # check reset time
                reset = get_reset_time(response)
                if reset != None:
                    # Sleeping for reset + 1 sec
                    print("\nSleep for " + str(reset + 1) + " sec and then continue...\n") 
                    time.sleep(reset + 1)
                # increase page num
                page_num = page_num + 1
            #--------------------------------------------------------------------
            # if there is searched data, write to file
            if searched_data != []:            
                searched_data = [j for i in searched_data for j in i]            
                if MERGE_TO_SINGLE_FILE == 1:
                    f = open(tns_search_file_path, 'w')
                    for el in searched_data:
                        f.write(el + '\n')
                    f.close()
                    if len(searched_data) > 2:
                        print ("\nTNS searched data returned " + str(len(searched_data) - 1) + " rows. File '" + \
                            tns_search_file + "' is successfully created.\n")
                    else: 
                        print ("\nTNS searched data returned 1 row. File '" + tns_search_file + "' is successfully created.\n")            
                else:                
                    if len(searched_data) > 2:
                        print ("TNS searched data returned " + str(len(searched_data) - 1) + " rows in total.\n")
                    else: 
                        print ("TNS searched data returned 1 row in total.\n")
            else:
                if MERGE_TO_SINGLE_FILE == 1:
                    print ("")
                print ("TNS searched data returned empty list. No file(s) created.\n")
                # remove empty folder
                if MERGE_TO_SINGLE_FILE == 0:
                    os.rmdir(tns_search_folder_path)
                    print ("Folder /" + tns_search_folder + "/ is removed.\n")

        return Table.read(tns_search_file_path,format='csv')
    return search_tns()


URL_PARAMETERS       = ["discovered_period_value", "discovered_period_units", "unclassified_at", "classified_sne", "include_frb",
                        "name", "name_like", "isTNS_AT", "public", "ra", "decl", "radius", "coords_unit", "reporting_groupid[]",
                        "groupid[]", "classifier_groupid[]", "objtype[]", "at_type[]", "date_start[date]",
                        "date_end[date]",  "discovery_mag_min", "discovery_mag_max", "internal_name", "discoverer", "classifier",
                        "spectra_count", "redshift_min", "redshift_max", "hostname", "ext_catid", "ra_range_min", "ra_range_max",
                        "decl_range_min", "decl_range_max", "discovery_instrument[]", "classification_instrument[]",
                        "associated_groups[]", "official_discovery", "official_classification", "at_rep_remarks", "class_rep_remarks",
                        "frb_repeat", "frb_repeater_of_objid", "frb_measured_redshift", "frb_dm_range_min", "frb_dm_range_max",
                        "frb_rm_range_min", "frb_rm_range_max", "frb_snr_range_min", "frb_snr_range_max", "frb_flux_range_min",
                        "frb_flux_range_max", "format", "num_page"]





def download_ep_data(username: str,
                     password: str,
                     ra: float,
                     dec: float,
                     start_time: str,
                     end_time: str,
                     destination_path: str,
                     radius: float = 0.01,
                     headless: bool = True,
                     instrument: str = 'FXT',
                     state_path: str = "ep_oauth_state.json"):
    """
    Download Einstein Probe FXT observation data for given coordinates and time range.

    Parameters
    ----------
    username : str
        EP account username.
    password : str
        EP account password.
    ra : float
        Target right ascension (deg).
    dec : float
        Target declination (deg).
    start_time : str
        Start time in "YYYY-MM-DD HH:MM:SS" format.
    end_time : str
        End time in "YYYY-MM-DD HH:MM:SS" format.
    destination_path : str
        Directory where data will be saved.
    radius : str, optional
        Search radius in degrees. Default = 0.01.
    headless : bool, optional
        Run browser in headless mode (default True).
    state_path : str, optional
        Path to save the Playwright state for login persistence.
    """

    # ====== internal constants ======
    PROTECTED_URL = "https://ep.bao.ac.cn/ep/data_center/fxt_obs/"
    if instrument == 'WXT':
        API_URL = 'https://ep.bao.ac.cn/ep/data_center/wxt_observation_data/api'
    elif instrument == 'FXT':
        API_URL = "https://ep.bao.ac.cn/ep/data_center/fxt_obs/api/"
    else:
        raise ValueError('Input valid instrument!')
    
    PER_PAGE_TIMEOUT = 5 * 60 * 1000
    ASYNC_MAX_WAIT = 10 * 60
    RETRY_TIMES = 2

    destination_path = Path(destination_path)
    destination_path.mkdir(parents=True, exist_ok=True)

    # ====== internal helper functions ======
    def _mkrow_dir(destination_path: Path, obs_id: str, detnam: str, version: str) -> Path:
        d = destination_path / f"{obs_id}_{detnam}_{version}"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _wait_async_link(page) -> Optional[str]:
        page.get_by_role("button", name="Download User data").click()
        page.wait_for_selector("#async-download-status", state="visible", timeout=30_000)
        t0 = time.time()
        while time.time() - t0 < ASYNC_MAX_WAIT:
            try:
                page.wait_for_function(
                    """() => {
                        const box = document.querySelector('#async-download-link');
                        const a = box ? box.querySelector('a') : null;
                        return box && getComputedStyle(box).display !== 'none' && a && a.href;
                    }""",
                    timeout=5_000
                )
                href = page.eval_on_selector("#async-download-link a", "el => el.href")
                return href
            except PWTimeout:
                continue
        return None

    def _download_user_zip(page, out_dir: Path, obs_id: str, detnam: str, version: str) -> Path:
        target = out_dir / f"{obs_id}_{detnam}_{version}_user.zip"
        if target.exists():
            print(f"  [skip] user zip exists: {target.name}")
            return target
        href = _wait_async_link(page)
        if not href:
            raise RuntimeError("Async user-data link did not appear within time limit.")
        with page.expect_download(timeout=PER_PAGE_TIMEOUT) as dl_info:
            page.click("#async-download-link a")
        dl = dl_info.value
        dl.save_as(target.as_posix())
        print(f"  [ok] user zip -> {target.name}")
        return target

    def _download_sources_csv(page, out_dir: Path, obs_id: str, detnam: str, version: str) -> Path:
        target = out_dir / f"{obs_id}_{detnam}_{version}_sources.csv"
        if target.exists():
            print(f"  [skip] sources csv exists: {target.name}")
            return target
        page.wait_for_selector("#download_src", timeout=30_000)
        with page.expect_download(timeout=PER_PAGE_TIMEOUT) as dl_info:
            page.click("#download_src")
        dl = dl_info.value
        dl.save_as(target.as_posix())
        print(f"  [ok] sources csv -> {target.name}")
        return target

    def _process_one_row(page, row: pd.Series, destination_path: Path):
        obs_id = str(row["obs_id"]).strip()
        detnam = str(row["detnam"]).strip()
        version = str(row.get("version", "02")).strip()
        url = f"https://ep.bao.ac.cn/ep/data_center/fxt_obs_detail/{obs_id}/{detnam}/{version}"
        print(f"\n==> {obs_id} {detnam} {version}")
        page.goto(url, wait_until="domcontentloaded", timeout=PER_PAGE_TIMEOUT)
        page.wait_for_selector("text=Get Data Files", timeout=30_000)
        page.wait_for_selector("text=Sources in the observation", timeout=30_000)
        out_dir = _mkrow_dir(destination_path, obs_id, detnam, version)
        try:
            _download_user_zip(page, out_dir, obs_id, detnam, version)
        except Exception as e:
            print(f"  [warn] user zip failed: {e}")
        try:
            _download_sources_csv(page, out_dir, obs_id, detnam, version)
        except Exception as e:
            print(f"  [warn] sources csv failed: {e}")

    def _run_batch(df: pd.DataFrame, destination_path: Path):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            ctx = browser.new_context(storage_state=state_path, accept_downloads=True)
            page = ctx.new_page()
            for i, row in df.iterrows():
                for attempt in range(1, RETRY_TIMES + 2):
                    try:
                        _process_one_row(page, row, destination_path)
                        break
                    except Exception as e:
                        print(f"  [err] row {i} attempt {attempt} failed: {e}")
                        if attempt <= RETRY_TIMES:
                            time.sleep(3)
                        else:
                            print("  [give up] move on.")
            browser.close()

    def _login(username, password):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            ctx = browser.new_context()
            page = ctx.new_page()
            page.goto(PROTECTED_URL, wait_until="domcontentloaded")
            if "oauth.china-vo.org" not in page.url:
                ctx.storage_state(path=state_path)
                cookies = ctx.cookies()
                browser.close()
                s = requests.Session()
                for c in cookies:
                    s.cookies.set(c["name"], c["value"], domain=c.get("domain"), path=c.get("path", "/"))
                return s
            page.wait_for_selector('input[name="username"]', timeout=60_000)
            page.fill('input[name="username"]', username)
            page.fill('input[name="password"]', password)
            if page.is_visible('input[name="captcha"]'):
                page.screenshot(path="login_need_captcha.png")
                code = input("验证码出现，请查看 login_need_captcha.png 并输入: ").strip()
                page.fill('input[name="captcha"]', code)
            page.get_by_role("button", name=re.compile("login", re.I)).click()
            try:
                page.wait_for_url(re.compile(r"^https://ep\.bao\.ac\.cn/.*"), timeout=60_000)
            except PWTimeout:
                page.wait_for_selector('a[href="/ep/user/logout"], img.avatar-xs, text=My Home',
                                       timeout=60_000)
            ctx.storage_state(path=state_path)
            cookies = ctx.cookies()
            browser.close()
        s = requests.Session()
        for c in cookies:
            s.cookies.set(c["name"], c["value"], domain=c.get("domain"), path=c.get("path", "/"))
        return s

    # ====== main logic ======
    session = _login(username, password)
    params = {
        "obs_id": "",
        "start_datetime": start_time,
        "end_datetime": end_time,
        "ra": ra,
        "dec": dec,
        "radius": str(radius),
    }
    response = session.post(API_URL, data=params)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data)
    if not df.empty:
        df = df.sort_values(["obs_start", "detnam"], ascending=[True, True]).reset_index(drop=True)
        df.to_csv(destination_path / "fxt_obs_list.csv", index=False, encoding="utf-8-sig")
        _run_batch(df, destination_path)
        print("✅ All downloads completed.")
    else:
        print("⚠️ No matching observations found.")


# Example:
# download_ep_data(
#     username="aujust",
#     password="Liang@981127",
#     ra=75.3897,
#     dec=-47.0878,
#     start_time="2025-09-27 00:00:00",
#     end_time="2025-10-02 00:00:00",
#     destination_path="/Volumes/T7/Shared_Files/EP/Results/SBO/data/AT2025zby/fxtl1"
# )