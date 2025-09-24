import SOCS_Xray
from astropy.table import Table
from astropy.time import Time

#Test get_Alerce
tnow = Time.now()
mjdfirst = tnow.mjd - 1
#query = SOCS_Xray.base_alerce_query(ndet=1,mjdfirst=mjdfirst)

#tbl = SOCS_Xray.get_Alerce(query)
#print(tbl)

#tbl = Table.read('/Users/liangrunduo/Desktop/Aujust/NAOC/EP/SOCS_data/tns_public_objects_old.csv',format='csv',header_start=1, data_start=2)
#tbl.write('/Users/liangrunduo/Desktop/Aujust/NAOC/EP/SOCS_data/tns_public_objects_old.csv',format='csv',overwrite=True)
#print(tbl)


pipe = SOCS_Xray.Pipeline(email='liangrd@bao.ac.cn',
                          password='Liang981127',
                          root='/Users/liangrunduo/Desktop/Aujust/NAOC/EP/SOCS_data')

pipe.run()

pipe.tns_match.pprint()
pipe.ztf_match.pprint()