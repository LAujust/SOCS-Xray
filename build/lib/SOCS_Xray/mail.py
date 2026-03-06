from .utils import *
import smtplib
from email.mime.text import MIMEText


def send_email(smtp_server:str,smtp_port:float,sender_email:str,receiver_emails:list,password:str,html_body:str,title='EP Counterpart Searching Notice'):
    """Send email to a list of address. 

    Args:
        smtp_server (str): SMTP server.
        smtp_port (float): SMTP port.
        sender_email (str): Sender email.
        receiver_emails (list): List of receiver emails.
        password (str): password.
        html_body (str): content.
        title (str, optional): Email title. Defaults to 'EP Counterpart Searching Notice'.
    """
    msg = MIMEText(html_body, "html", 'utf-8')
    msg["From"] = sender_email
    msg["To"] = ", ".join(receiver_emails)
    msg["Subject"] = title
    
    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_emails, msg.as_string())
    except Exception as e:
        print(f'Fial on SSH: {e}')
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_emails, html_body)
        except Exception as e:
            print(f'Fial to send email: {e}')
            

    print("✅ HTML email sent!")
    
    
    