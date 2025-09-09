import SOCS_Xray
from astropy.table import Table

#SOCS_Xray.fetch.get_TNS(save_dir='./data')
#SOCS_Xray.fetch.update_WXT_source_list('liangrd@bao.ac.cn','Liang981127','./data')

data = Table.read('/Volumes/T7/Shared_Files/EP/Projects/SOCS-Xray/data/tns_public_objects.csv.zip')