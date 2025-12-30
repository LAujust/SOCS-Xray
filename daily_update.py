import sys, os
import warnings
warnings.filterwarnings("ignore")
import SOCS_Xray
from astropy.table import Table
from astropy.time import Time

tdic_email = os.environ["TDIC_EMAIL"]
tdic_password = os.environ["TDIC_PASSWORD"]
smtp_server = os.environ["SMTP_SERVER"]
smtp_port = os.environ["SMTP_PORT"]
sender_email = os.environ["SENDER_EMAIL"]
sender_password = os.environ["SENDER_PASSWORD"]
SEND_EMAIL = False
dt = [-7,30]


# #=========test TNS-API=========#
# import json
# import requests
# def search_TNS_bot(
#     api_key,
#     bot_id,
#     bot_name,
#     search_params,
# ):
#     url = "https://www.wis-tns.org/api/get/search"

#     headers = {
#         "User-Agent": f'tns_marker{{"tns_id":{bot_id},"type":"bot","name":"{bot_name}"}}'
#     }

#     payload = {
#         "api_key": api_key,
#         "data": json.dumps(search_params)
#     }

#     r = requests.post(url, headers=headers, data=payload, timeout=60)

#     if r.status_code != 200:
#         raise RuntimeError(f"TNS search failed: {r.status_code}\n{r.text}")

#     res = r.json()

#     if "data" not in res:
#         print("Empty TNS reply")
#         return None

#     data = res["data"]
#     return data

# #========================================================#
# API_KEY = '48aa6e2dfcb5893b987dda29b3f3938e97e8db43'
# BOT_ID = '164028'
# BOT_NAME = 'bot_BC'

# search_parameters={
#         "reported_period_value": "3",
#         "reporteded_period_units": "days",
#         "format": "csv",
#         "num_page": "100",
        
#     }
# data = search_TNS_bot(api_key=API_KEY,bot_id=BOT_ID,bot_name=BOT_NAME,search_params=search_parameters)
# objids = [item['objid'] for item in data]
# objnames = [item['objname'] for item in data]
# print(objnames)

#Sweep log file
log_file = "daily.log"
# 清空日志文件
with open(log_file, "w") as f:
    pass  # 打开写模式就会清空文件

with open("./data/mail_list.txt") as f:
    success_receiver = [line.strip() for line in f if line.strip()]

# success_receiver = ['liangrd@bao.ac.cn','liwx@bao.ac.cn','wmy@nao.cas.cn',
#                   'hsun@nao.cas.cn','ccjin@bao.ac.cn','dyli@nao.cas.cn',
#                   'liuyuan@bao.ac.cn']
null_receiver = ['liangrd@bao.ac.cn']


pipe = SOCS_Xray.Pipeline(email=tdic_email,
                          password=tdic_password,
                          root='./data',) 

pipe.run(dt=dt,update_result=True,show_progress=True)

if len(pipe.uniform_match) > 0:
    print(pipe.uniform_match)
    if SEND_EMAIL:
        SOCS_Xray.send_email(smtp_server=smtp_server,
                            sender_email=sender_email,
                            smtp_port=smtp_port,
                            receiver_emails=success_receiver,
                            password=sender_password,
                            html_body=pipe.uniform_html)
else:
    null_notice = """
                    <html>
                    <body>
                    <p>No matched candidates at %s. 
                    <p>Matched with %s TNS sources, %s ZTF sources. 
                                            <p>Running time: %.2f seconds. 
                    <p>Best regards,<br>Runduo</p>
                    </body>
                    </html>
                    """%(Time.now(),len(pipe.TNS_table),len(pipe.ZTF_clean),pipe.elapsed_time)
    receiver_emails = null_receiver
    if SEND_EMAIL:
        SOCS_Xray.send_email(smtp_server=smtp_server,
                            sender_email=sender_email,
                            smtp_port=smtp_port,
                            receiver_emails=receiver_emails,
                            password=sender_password,
                            html_body=null_notice)
    print('No matched sources at %s'%(Time.now()))