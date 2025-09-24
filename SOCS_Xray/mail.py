from .utils import *
import smtplib
from email.mime.text import MIMEText

def myaccount():
    smtp_server = 'mail.ustc.edu.cn'
    smtp_port = 465
    password = 'by9RhYneE6sCDMji'
    sender_email = 'aujust@mail.ustc.edu.cn'
    receiver_email = 'liangrd@bao.ac.cn'

def send_email(smtp_server,smtp_port,sender_email,receiver_emails,password,html_body,title='EP Counterpart Searching Notice'):
    msg = MIMEText(html_body, "html", 'utf-8')
    msg["From"] = sender_email
    msg["To"] = ", ".join(receiver_emails)
    msg["Subject"] = title
    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_emails, msg.as_string())
    # except:
    #     with smtplib.SMTP(smtp_server, smtp_port) as server:
    #         server.starttls()
    #         server.login(sender_email, password)
    #         server.sendmail(sender_email, receiver_emails, html_body)

    print("✅ HTML email sent!")
    
    
    