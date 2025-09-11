import SOCS_Xray
from astropy.table import Table

#Test get_Alerce
query = """
SELECT table_name  FROM information_schema.tables
WHERE table_schema='alerce'
ORDER BY table_name;
"""

tbl = SOCS_Xray.get_Alerce(query)
print(tbl)