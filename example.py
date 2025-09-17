import SOCS_Xray
from astropy.table import Table
from astropy.time import Time

#Test get_Alerce
tnow = Time.now()
mjdfirst = tnow.mjd - 1
query = SOCS_Xray.base_alerce_query(ndet=1,mjdfirst=mjdfirst)

tbl = SOCS_Xray.get_Alerce(query)
print(tbl)