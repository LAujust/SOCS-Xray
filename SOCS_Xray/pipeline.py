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
            if not os.path.exists(os.path.join(self.root,'matched.csv')):
                self.matched = Table()
                self.matched.write(os.path.join(self.root,'matched.csv'),format='csv',overwrite=True)
                print('Starting with NULL dataset. ')
            else:
                self.matched = Table.read(os.path.join(self.root,'matched.csv'),format='csv')
                print('Matched table loaded. ')
                
                
    def run(self,dt=30,ndays=10,show_progress=True,wxt_radii=3.5,fxt_radii=20,update_result=False):
        
        if show_progress:
            pbar = ' ================ '
            step = 0
            #pbar = tqdm(total=8, desc="Running Pipelline", ncols=100, dynamic_ncols=True)
        else:
            pbar = None
            
        #updata ep_source
        if pbar:
            step += 1
            print(pbar + '[%s]: Updateing WXT_source_list'%step + pbar)
            # pbar.set_description("Updateing WXT_source_list")
            # pbar.update(1)
            
        self.ep_source = update_WXT_source_list(EMAIL=self.account['email'],PASSWORD=self.account['password'],save_dir=self.root)
        EP_c = SkyCoord(self.ep_source['ra'],self.ep_source['dec'],unit=u.deg)
        
        #@@@ Update TNS @@@
        #@@@ WXT-TNS @@@
        if pbar:
            step += 1 
            print(pbar + '[%s]: Processing WXT-TNS'%step + pbar)
            
        self.update_TNS(ndays=ndays)
        TNS_c = SkyCoord(self.TNS_table['o_ra'],self.TNS_table['o_dec'],unit=u.deg)
            
        source_matched_idx, cat_matched_idx, cat_matched_sep = match_cat(EP_c,TNS_c,radius=wxt_radii*u.arcmin,seperation=True)
        EP_matched = self.ep_source[source_matched_idx]
        TNS_matched = self.TNS_table[cat_matched_idx]

        EP_matched = EP_matched['category','simbad_name','tags','id']
        TNS_matched = TNS_matched
        table_merge = hstack((EP_matched,TNS_matched))
        table_merge['separation (arcsec)'] = cat_matched_sep.arcsec
        table_of_highlight = Table()
        
        if len(EP_matched) > 0:
            tns_time = TNS_matched['firstmjd']
            wxt_time_raw = request_obs_time(ids=EP_matched['id'],EMAIL=self.account['email'],PASSWORD=self.account['password'])
            wxt_time = [d if d is not None else '2030-01-01T00:00:00Z' for d in wxt_time_raw]
            obs_time = Time(wxt_time)
            delta_t = tns_time - obs_time.mjd
            table_merge['dt'] = delta_t
            self.tns_match = table_merge[(table_merge['dt']<dt) & (table_merge['dt']>-dt)]
        else:
            self.tns_match = Table()
            
            
            
        #@@@ WXT-ZTF @@@
        if pbar:
            step += 1
            print(pbar + '[%s]: Processing WXT-ZTF'%step + pbar)
            
        self.update_ZTF(ndays=ndays)
        ZTF_c = SkyCoord(self.ZTF_clean['o_ra'],self.ZTF_clean['o_dec'],unit=u.deg)

        source_matched_idx, cat_matched_idx, cat_matched_sep = match_cat(EP_c,ZTF_c,radius=wxt_radii*u.arcmin,seperation=True)
        EP_matched = self.ep_source[source_matched_idx]
        ZTF_matched = self.ZTF_clean[cat_matched_idx]

        table_merge = hstack((EP_matched,ZTF_matched))
        table_merge['separation (arcsec)'] = cat_matched_sep.arcsec

        if len(EP_matched) > 0:
            ztf_time = Time(ZTF_matched['firstmjd'],format='mjd')
            wxt_time_raw = request_obs_time(ids=EP_matched['id'],EMAIL=self.account['email'],PASSWORD=self.account['password'])
            wxt_time = [d if d is not None else '2030-01-01T00:00:00Z' for d in wxt_time_raw]
            obs_time = Time(wxt_time)
            delta_t = ztf_time.mjd - obs_time.mjd
            table_merge['dt'] = delta_t

            #table_merge_unique = unique(table_merge,keys='oid')
            #table_merge = table_merge_unique

            #ndet = 1
            table_merge_1 = table_merge[table_merge['ndet']==1]
            table_of_highlight_1 = table_merge_1[(table_merge_1['dt']<1) & (table_merge_1['dt']>-1)]

            #ndet > 1
            table_merge_2 = table_merge[table_merge['ndet']>1]
            table_of_highlight_2 = table_merge_2[(table_merge_2['dt']<dt) & (table_merge_2['dt']>-dt)]

            table_of_highlight = vstack((table_of_highlight_1,table_of_highlight_2))
            self.ztf_match = table_of_highlight
        else:
            self.ztf_match = Table()
            
            
        
        #@@@ FXT-TNS @@@
        if pbar:
            step += 1
            print(pbar + '[%s]: Processing FXT-TNS'%step + pbar)
            
        self.fxt_tns_match = search_fxt_from_table(self.TNS_table[:100],email=self.account['email'],password=self.account['password'],ra_col='o_ra',dec_col='o_dec',radii=fxt_radii)
        if len(self.fxt_tns_match) > 0:
            self.fxt_tns_match = self.fxt_tns_match[(self.fxt_tns_match['dt']<dt) & (self.fxt_tns_match['dt']>-dt)]
            
        #@@@ FXT-ZTF @@@
        if pbar:
            step += 1
            print(pbar + '[%s]: Processing FXT-ZTF'%step + pbar)
            
            
        if len(self.ZTF_clean) > 2000:
            ZTF_clean_fxt = self.ZTF_clean[self.ZTF_clean['ndet']>1]
            print('Processing ndet > 1 with %s sources'%len(ZTF_clean_fxt))
        else:
            ZTF_clean_fxt = self.ZTF_clean
        self.fxt_ztf_match = search_fxt_from_table(ZTF_clean_fxt ,email=self.account['email'],password=self.account['password'],ra_col='o_ra',dec_col='o_dec',radii=fxt_radii)
        if len(self.fxt_ztf_match) > 0:
            self.fxt_ztf_match = self.fxt_ztf_match[(self.fxt_ztf_match['dt']<dt) & (self.fxt_ztf_match['dt']>-dt)]
            
            
            
        #@@@ Resemble Tables @@@
        if pbar:
            step += 1
            print(pbar + '[%s]: Resembling Tables'%step + pbar)
            
        col_names = ['ep_name','oid','o_ra','o_dec','separation (arcsec)','dt','link','fxt_name','pipeline']
        col_types = ['U30','U30','f8','f8','f8','f8','U100','U30','U30']
        res_table = Table(names=col_names,dtype=col_types)
        
        if len(self.tns_match) > 0:
            tns_match = self.tns_match
            tns_match['fxt_name'] = ['None'] * len(tns_match)
            tns_match['pipeline'] = ['WXT-TNS'] * len(tns_match)
            tns_match.rename_columns(['simbad_name'],['ep_name'])
            tns_match = tns_match[col_names]
            for col,col_type in zip(col_names,col_types):
                tns_match[col].astype(col_type)
            res_table = vstack((res_table,tns_match[col_names]))
        
        if len(self.ztf_match) > 0:
            ztf_match = self.ztf_match
            ztf_match['fxt_name'] = ['None'] * len(ztf_match)
            tns_match['pipeline'] = ['WXT-ZTF'] * len(ztf_match)
            ztf_match.rename_columns(['simbad_name'],['ep_name'])
            ztf_match = ztf_match[col_names]
            for col,col_type in zip(col_names,col_types):
                ztf_match[col].astype(col_type)
            res_table = vstack((res_table,ztf_match[col_names]))
            
        if len(self.fxt_tns_match) > 0:
            fxt_tns_match = self.fxt_tns_match
            fxt_tns_match['pipeline'] = ['FXT-TNS'] * len(fxt_tns_match)
            fxt_tns_match.rename_columns(['target_name'],['ep_name'])
            fxt_tns_match = fxt_tns_match[col_names]
            for col,col_type in zip(col_names,col_types):
                fxt_tns_match[col].astype(col_type)
            res_table = vstack((res_table,fxt_tns_match[col_names]))
            
        if len(self.fxt_ztf_match) > 0:
            fxt_ztf_match = self.fxt_ztf_match
            fxt_ztf_match['pipeline'] = ['FXT-ZTF'] * len(fxt_ztf_match)
            fxt_ztf_match.rename_columns(['target_name'],['ep_name'])
            fxt_ztf_match = fxt_ztf_match[col_names]
            for col,col_type in zip(col_names,col_types):
                fxt_ztf_match[col].astype(col_type)
            res_table = vstack((res_table,fxt_ztf_match[col_names]))
            
        self.uniform_match = res_table
        
        
        #@@@ Mail Content @@@
        if pbar:
            step += 1
            print(pbar + '[%s]: Preparing Emails'%step + pbar)
            
        LABELS = ['WXT-TNS','WXT-ZTF','FXT-TNS','FXT-ZTF']
        html_parts = []
        for i,tbl in enumerate([self.tns_match,self.ztf_match,self.fxt_tns_match,self.fxt_ztf_match]):
            if len(tbl) > 0:
                df = tbl.to_pandas()
                html_table = df.to_html(border=1,
                            index=False,
                            justify="center",
                            col_space=80)
                html_parts.append(f"<h3>{LABELS[i]}</h3>{html_table}")
        if len(html_parts) > 0:
            self.raw_html = f"""
                <html>
                <body>
                    {"<br>".join(html_parts)}
                    <br>
                    <p>This is preliminary result from EP-OT searching. 
                    <p>Best regards,<br>Runduo</p>
                </body>
                </html>
                """
                
        if pbar:
            step += 1
            print(pbar + '[%s]: Saving Results'%step + pbar)
            
        if len(self.uniform_match) > 0:
            
            if update_result:
                self.matched = vstack((self.matched,self.uniform_match))
                self.matched.write(os.path.join(self.root,'matched.csv'),format='csv',overwrite=True)                                    
                        
                
            df = self.uniform_match.to_pandas()
            html_table = df.to_html(border=1,
                            index=False,
                            justify="center",
                            col_space=80)
            self.uniform_html = f"""
                                    <html>
                                    <body>
                                        "<br>"{html_table}
                                        <br>
                                        <p>This is preliminary result from EP-OT searching. 
                                        <p>Best regards,<br>Runduo</p>
                                    </body>
                                    </html>
                                    """

        
                
        
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
    
    def update_TNS(self,ndays=2):
        # if os.path.exists(os.path.join(self.root,'tns_public_objects.csv')):   
        #     old = Table.read(os.path.join(self.root,'tns_public_objects.csv'),format='csv')
        #     new = get_TNS(save_dir=self.root)
        #     self.TNS_table = setdiff(new,old,keys=["name_prefix","name"])
        # else:
        try:
            self.TNS_table = get_TNS(save_dir=self.root)
                
            self.TNS_table.write(os.path.join(self.root,'tns_public_objects.csv'),format='csv',overwrite=True)
                
            tns_name = [self.TNS_table['name_prefix'][i]+self.TNS_table['name'][i] for i in range(len(self.TNS_table))]
            self.TNS_table['tns_name'] = tns_name
            self.TNS_table['firstmjd'] = Time(self.TNS_table['discoverydate']).mjd
            self.TNS_table['link'] = ['https://www.wis-tns.org/object/'+self.TNS_table['name'][i] for i in range(len(self.TNS_table))]
            
            self.TNS_table.rename_columns(['ra','declination','tns_name'],['o_ra','o_dec','oid'])
            self.TNS_table = self.TNS_table['oid','o_ra','o_dec','discoverydate','firstmjd','link']
            
            tnow = Time.now()
            mjdmin = tnow.mjd - ndays
            self.TNS_table = self.TNS_table[self.TNS_table['firstmjd']>=mjdmin]
        except:
            self.TNS_table = search_TNS(user_id="3740",user_name='Aujust',save_dir=self.root)
            coord = SkyCoord(self.TNS_table['RA'],self.TNS_table['DEC'],unit=(u.hourangle, u.deg))
            self.TNS_table['RA'] = coord.ra.deg
            self.TNS_table['DEC'] = coord.dec.deg
            self.TNS_table['name'] = [self.TNS_table['Name'][i].split(' ')[-1] for i in range(len(self.TNS_table))]
            self.TNS_table['link'] = ['https://www.wis-tns.org/object/'+self.TNS_table['name'][i] for i in range(len(self.TNS_table))]
            self.TNS_table['firstmjd'] = Time(self.TNS_table['Discovery Date (UT)']).mjd
            self.TNS_table.rename_columns(['Name','RA','DEC','Discovery Date (UT)'],
                                            ['oid','o_ra','o_dec','discoverydate'])
            self.TNS_table['oid','o_ra','o_dec','discoverydate','firstmjd','link']
        
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
                                        ['oid','o_ra','o_dec','firstmjd','class'])
        elif alerce_table is not None and lasair_table is None:
            ZTF_clean = alerce_table['oid','meanra','meandec','probability','firstmjd','ndet','class_name']
            ZTF_clean.rename_columns(['meanra','meandec','class_name'],['o_ra','o_dec','class'])
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

        ZTF_clean_unique = unique(ZTF_clean,keys='oid')
        self.ZTF_clean = ZTF_clean_unique['oid','o_ra','o_dec','firstmjd','link','ndet']
        
        
    