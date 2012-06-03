#-*- coding:utf-8 -*-

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import os
 

_TO_UNICODE_TYPES = (unicode, type(None))
def to_unicode(value):
    if isinstance(value, _TO_UNICODE_TYPES):
        return value
    assert isinstance(value, bytes)
    return value.decode("utf-8")

    
def send_mail(to, fro, subject, text, html, files=[],server="localhost"):
    assert type(to)==list
    assert type(files)==list
 
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['From'] = fro
    msg['To'] = COMMASPACE.join(to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = to_unicode(subject)
 
    if text:
        msg.attach( MIMEText(text, 'plain', 'utf-8' ))
    if html:
        msg.attach( MIMEText(html, 'html', 'utf-8'))
 
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

if __name__ == "__main__":
    send_mail(['laiwei_ustc <laiwei.ustc@gmail.com>'],
        'Today of The Past<help@thepast.me>',
        'thepast.me | 历史上的今天',
        'http://thepast.me个人杂志计划', 'html内容',
        ['/home/work/proj/thepast/past/static/img/avatar.png'])
