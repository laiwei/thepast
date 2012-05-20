#-*- coding:utf-8 -*-

import sys
sys.path.append("../")

activate_this = '../env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import datetime
import time

from past.utils import wrap_long_line, filters 
from past.utils.escape import clear_html_element
from past.utils.sendmail import send_mail
from past.model.status import get_status_ids_today_in_history, \
        get_status_ids_yesterday, Status
from past.model.user import User
from past.store import db_conn
from past import config

def send_today_in_history(user_id):
    u = User.get(user_id)
    if not u:
        return

    setting = u.get_profile_item("email_remind_today_in_history")
    if setting == 'N':
        print '---user %s does not like to receive remind mail' % u.id
        return

    email = u.get_email()
    if not email:
        print '---- user %s no email' % u.id
        return
    
    yesterday_ids = get_status_ids_yesterday(u.id, 
            day=(datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"))
    status_of_yesterday = Status.gets(yesterday_ids)

    history_ids = get_status_ids_today_in_history(u.id, 
            day=datetime.datetime.now().strftime("%Y-%m-%d"))
    status_of_today_in_history = Status.gets(history_ids)

    intros = [u.get_thirdparty_profile(x).get("intro") for x in config.OPENID_TYPE_DICT.values()]
    intros = filter(None, intros)
    
    history_ids = get_status_ids_today_in_history(u.id, 
            day=datetime.datetime.now().strftime("%Y-%m-%d"))
    d = {}
    for s in Status.gets(history_ids):
        t = s.create_time.strftime("%Y-%m-%d")
        if d.has_key(t):
            d[t].append(s)
        else:
            d[t] = [s]
    status_of_today_in_history = d
    from past.consts import YESTERDAY


    if not (status_of_yesterday or status_of_today_in_history):
        print '--- user %s has no status in history' % u.id
        return

    from jinja2 import Environment, PackageLoader
    env = Environment(loader=PackageLoader('past', 'templates'))
    env.filters['wrap_long_line'] = wrap_long_line
    env.filters['nl2br'] = filters.nl2br
    env.filters['clear_html_element'] = clear_html_element
    t = env.get_template('mail.html')
    m = t.module


    html = m.status_in_past(status_of_yesterday, status_of_today_in_history, YESTERDAY, config, intros)
    html = html.encode("utf8")

    subject = '''来自thepast.me的提醒 %s''' % datetime.datetime.now().strftime("%Y-%m-%d")
    text = ''
    
    print '--- send reminding to %s %s' %(user_id, email)
    send_mail(["%s" % email], "help@thepast.me", subject, text, html, files=[], server="localhost")

def send_pdf(user_id):
    u = User.get(user_id)

    if not u:
        return

    setting = u.get_profile_item("email_remind_today_in_history")
    if setting == 'N':
        print '---user %s does not like to receive remind mail' % u.id
        return

    email = u.get_email()
    if not email:
        print '---- user %s no email' % u.id
        return

    subject = '''你在thepast.me上的timeline PDF版本'''
    text = '''Hi，感谢你使用thepast.me来聚合、管理、备份自己的timeline.

离线PDF版本现在可以下载了，请猛击 http://thepast.me/%s/pdf

http://thepast.me | 个人杂志计划
thanks''' % user_id
    
    print '--- send pdf file to %s %s' %(user_id, email)
    send_mail(["%s" % email], "help@thepast.me", subject, text, '', files=[], server="localhost")

if __name__ == '__main__':
    cursor = db_conn.execute("select max(id) from user")
    row = cursor.fetchone()
    cursor and cursor.close()
    max_uid = row and row[0]
    max_uid = int(max_uid)
    t = 0
    for uid in xrange(4,max_uid + 1):
        if t >= 100:
            t = 0
            time.sleep(5)
        send_today_in_history(uid)
        time.sleep(5)
        t += 1

