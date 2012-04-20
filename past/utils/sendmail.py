#-*- coding:utf-8 -*-

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import os
 
def send_mail(to, fro, subject, text, html, files=[],server="localhost"):
    assert type(to)==list
    assert type(files)==list
 
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['From'] = fro
    msg['To'] = COMMASPACE.join(to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
 
    if text:
        msg.attach( MIMEText(text, 'plain' ))
    if html:
        msg.attach( MIMEText(html, 'html'))
 
    for file in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(file,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"'
                       % os.path.basename(file))
        msg.attach(part)
 
    smtp = smtplib.SMTP(server)
    smtp.sendmail(fro, to, msg.as_string() )
    smtp.close()

#send_mail(['laiwei_ustc <laiwei.ustc@gmail.com>'],'thepast <help@thepast.me>','thepast.me 历史上的今天','http://thepast.me个人杂志计划',['/home/work/proj/thepast/past/static/img/avatar.png','/home/work/proj/thepast/var/down/pdf/thepast.me_4_201203.pdf'])
