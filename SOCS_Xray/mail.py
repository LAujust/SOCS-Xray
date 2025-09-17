from .utils import *
import smtplib
from email.message import EmailMessage

def myaccount():
    smtp_server = 'mail.ustc.edu.cn'
    smtp_port = 465
    password = 'by9RhYneE6sCDMji'
    sender_email = 'aujust@mail.ustc.edu.cn'
    receiver_email = 'liangrd@bao.ac.cn'
