from .utils import *

def search_fxt_from_table(input_file, email, password, ra_col, dec_col, radii, output_file, oid='oid', cols=None):
    """
    Query EP API for FXT sources given RA/Dec table and multiple search radii.
    Results are merged back into the input table.

    Parameters
    ----------
    input_file : str
        Path to CSV/Excel file containing RA/Dec columns.
    ra_col, dec_col : str
        Column names for RA and Dec in the input table.
    radii : float
        search radii in arcseconds.
    output_file : str
        Path to save merged table with search results.
    oid : str
    'oid' or 'full_name'
    """
    
    # ===== Step 1: Load table =====
    if input_file.endswith(".csv"):
        df = pd.read_csv(input_file)
    else:
        df = pd.read_excel(input_file)
        
    if cols:
        df = df[cols]

    # Ensure RA/Dec columns exist
    if ra_col not in df.columns or dec_col not in df.columns:
        raise ValueError(f"Columns {ra_col} and/or {dec_col} not found in table.")

    # ===== Step 2: Get API token =====
    EP_TOKEN_URL = "https://ep.bao.ac.cn/ep/api/get_tokenp"
    EP_EMAIL = email
    EP_PASSWORD = password

    try:
        resp = requests.post(
            EP_TOKEN_URL,
            json={"email": EP_EMAIL, "password": EP_PASSWORD},
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        resp.raise_for_status()
        token = resp.json().get('token')
    except Exception as e:
        raise RuntimeError(f"Failed to get token: {e}")

    # ===== Step 3: API endpoint =====
    ep_batch_url = "https://ep.bao.ac.cn/ep/data_center/api/batch_fxt_sourceobs_by_triplets"

    # ===== Step 4: Prepare output =====
    # Make columns for each radius
    fxt_base_cols = ["_create_time", "fxt_name", "target_name", "detnam"]
    for r in fxt_base_cols:
        df[r] = None
        
    df['dt'] = None
    columns = df.columns

    # ===== Step 5: Process in batches of ≤50 =====
    batch_size = 50
    total_batches = math.ceil(len(df) / batch_size)
    
    df_filtered = None

    for batch_idx in range(total_batches):
        batch_df = df.iloc[batch_idx*batch_size:(batch_idx+1)*batch_size]
        triplets_base = [
            {"id": int(idx), "ra": float(row[ra_col]), "dec": float(row[dec_col])}
            for idx, row in batch_df.iterrows()
        ]
        
        oids = [
            row[oid]
            for idx, row in batch_df.iterrows()
        ]

        if radii:
            print(f"Processing batch {batch_idx+1}/{total_batches} — radius {radii} arcsec")

            batch_payload = {
                "triplets": triplets_base,
                "radius_arcsec": radii
            }

            try:
                ep_resp = requests.post(
                    ep_batch_url,
                    json=batch_payload,
                    headers={
                        "tdic-token": token,
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    params={"token": token},
                    timeout=600
                )
                ep_resp.raise_for_status()
                observations_data = ep_resp.json()
            

                if observations_data.get('status') == 'success':
                    
                    data_dict = observations_data.get('data', {})
                    for entry in triplets_base:
                        match_info = data_dict.get(str(entry["id"]), None)
                        if match_info:
                            match_table_raw = pd.DataFrame(match_info)
                            #match_table_raw2 = Table.from_pandas(match_table_raw)
                            #print(match_table_raw2.pprint(max_width=-1))
                            match_table = match_table_raw.drop_duplicates(subset="fxt_name", keep="last")
                            
                            match_table = Table.from_pandas(match_table)
                            #match_table.pprint(max_width=-1)
                            match_table = match_table[["_create_time", "fxt_name", "target_name", "detnam"]]
                            create_times = match_table["_create_time"].value
                            cts = [datetime.strptime(i, "%a, %d %b %Y %H:%M:%S %Z") for i in create_times]
                            ct = [Time(i.isoformat().replace('T',' ')).iso for i in cts]
                            match_table["_create_time"] = ct
                            
                            df_sel = df.loc[[entry["id"]],:]
                            df_dup = pd.DataFrame(
                                    np.repeat(df_sel.values, len(match_table), axis=0), 
                                    columns=columns
                                )
                            for r in fxt_base_cols:
                                df_dup.loc[:, r] = match_table[r]
                            
                            if df_filtered is None:
                                df_filtered = df_dup
                            else:
                                df_filtered = pd.concat([df_filtered,df_dup])

                else:
                    print(f"API error: {observations_data.get('message', 'Unknown error')}")

            except Exception as e:
                print(f"Failed batch {batch_idx+1} radius {radii}: {e}")
                print(df_filtered)
                
    #df_filtered = df[df["fxt_name"].notnull() & (df["fxt_name"] != "")]
    #table_filtered.pprint(max_width=-1)
    if df_filtered is not None:
        #print(df_filtered)
        table_filtered = Table.from_pandas(df_filtered)
        #print(np.array(table_filtered['_create_time'].value))
        #print(Time(table_filtered['_create_time'].value[0]).mjd)
        try:  
            dt = Time(table_filtered['discoverydate']).mjd - Time(table_filtered['_create_time'].value).mjd
            df_filtered['dt'] = Time(table_filtered['discoverydate']).mjd - Time(table_filtered['_create_time'].value).mjd
        except:
             df_filtered['dt'] = table_filtered['firstmjd'] -  Time(table_filtered['_create_time'].value).mjd
        # ===== Step 6: Save merged table =====
        df_filtered = df_filtered.rename(columns={'_create_time':'fxt_create_time'})
        df_filtered.to_csv(output_file, index=False)
        print(f"Saved results to {output_file}")
    else:
        print('No matched sources for %s'%(output_file))