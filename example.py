import SOCS_Xray
from astropy.table import Table

tns_table = SOCS_Xray.fetch.get_TNS(save_dir='/Users/liangrunduo/Desktop/Aujust/NAOC/EP/SOCS_data')
print(tns_table['discoverydate'])
#SOCS_Xray.fetch.update_WXT_source_list('liangrd@bao.ac.cn','Liang981127','./data')

#data = Table.read('/Volumes/T7/Shared_Files/EP/Projects/SOCS-Xray/data/tns_public_objects.csv.zip')