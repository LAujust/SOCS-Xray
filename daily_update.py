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