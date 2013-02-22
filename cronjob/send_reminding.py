#-*- coding:utf-8 -*-

import sys
sys.path.append("../")

activate_this = '../env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import datetime
import time
import traceback

from past.utils import wrap_long_line, filters 
from past.utils.escape import clear_html_element
from past.utils.sendmail import send_mail
from past.model.status import get_status_ids_today_in_history, \
        get_status_ids_yesterday, Status
from past.model.user import User
from past.store import db_conn
from past import config
from past.api.error import OAuthTokenExpiredError

def send_today_in_history(user_id, now=None, include_yestorday=False):
    if not now:
        now = datetime.datetime.now()

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
    
    history_ids = get_status_ids_today_in_history(u.id, now)
    status_of_today_in_history = Status.gets(history_ids)
    
    if include_yestorday:
        yesterday_ids = get_status_ids_yesterday(u.id, now) 
        status_of_yesterday = Status.gets(yesterday_ids)
    else:
        status_of_yesterday = None

    intros = [u.get_thirdparty_profile(x).get("intro") for x in config.OPENID_TYPE_DICT.values()]
    intros = filter(None, intros)
    
    d = {}
    for s in Status.gets(history_ids):
        t = s.create_time.strftime("%Y-%m-%d")
        if d.has_key(t):
            d[t].append(s)
        else:
            d[t] = [s]
    status_of_today_in_history = d
    from past.consts import YESTERDAY

    if not (status_of_today_in_history or (include_yestorday and status_of_yesterday)):
        print '--- user %s has no status in history' % u.id
        return

    from jinja2 import Environment, PackageLoader
    env = Environment(loader=PackageLoader('past', 'templates'))
    env.filters['wrap_long_line'] = wrap_long_line
    env.filters['nl2br'] = filters.nl2br
    env.filters['stream_time'] = filters.stream_time
    env.filters['clear_html_element'] = clear_html_element
    env.filters['isstr'] = lambda x: isinstance(x, basestring)
    t = env.get_template('mail.html')
    m = t.module


    if now:
        y = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        y = YESTERDAY
    html = m.status_in_past(status_of_yesterday, status_of_today_in_history, y, config, intros)
    html = html.encode("utf8")

    subject = '''thepast.me|整理自己的故事 %s''' % now.strftime("%Y-%m-%d")
    text = ''
    
    print '--- send reminding to %s %s' %(user_id, email)
    send_mail(["%s" % email], "thepast<help@thepast.me>", subject, text, html)

def send_yesterday(user_id, now=None):
    if not now:
        now = datetime.datetime.now()

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
    
    yesterday_ids = get_status_ids_yesterday(u.id, now) 
    status_of_yesterday = Status.gets(yesterday_ids)

    intros = [u.get_thirdparty_profile(x).get("intro") for x in config.OPENID_TYPE_DICT.values()]
    intros = filter(None, intros)

    from past.consts import YESTERDAY

    if not status_of_yesterday:
        print '--- user %s has no status in yesterday' % u.id
        return

    from jinja2 import Environment, PackageLoader
    env = Environment(loader=PackageLoader('past', 'templates'))
    env.filters['wrap_long_line'] = wrap_long_line
    env.filters['nl2br'] = filters.nl2br
    env.filters['stream_time'] = filters.stream_time
    env.filters['clear_html_element'] = clear_html_element
    t = env.get_template('mail.html')
    m = t.module


    if now:
        y = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        y = YESTERDAY
    html = m.status_in_past(status_of_yesterday, None, y, config, intros)
    html = html.encode("utf8")

    subject = '''thepast.me|整理自己的故事 %s''' % now.strftime("%Y-%m-%d")
    text = ''
    
    print '--- send reminding to %s %s' %(user_id, email)
    send_mail(["%s" % email], "thepast<help@thepast.me>", subject, text, html)

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
    send_mail(["%s" % email], "thepast<help@thepast.me>", subject, text, "")

def send_reconnect(user_id):
    u = User.get(user_id)

    if not u:
        return

    setting = u.get_profile_item("email_remind_today_in_history")
    if setting == 'N':
        print '---user %s does not like to receive remind mail' % u.id
        return

    excps = [OAuthTokenExpiredError(user_id, x) for x in config.OPENID_TYPE_DICT.values()]
    expires_site = {}
    for e in excps:
        t = e.is_exception_exists()
        if t:
            expires_site[e.openid_type] = t

    if not expires_site:
        print '--- user %s has no expired connection' % u.id
        return
    else:
        print '--- user %s expired connection: %s' %(u.id, expires_site)

    email = u.get_email()
    if not email:
        print '---- user %s no email' % u.id
        return

    names = []
    reconnect_urls = []
    for x in expires_site.keys():
        names.append(config.OPENID_TYPE_NAME_DICT.get(x, ""))
        reconnect_urls.append("http://thepast.me/connect/%s" % config.OPENID_TYPE_DICT_REVERSE.get(x))

    subject = '''thepast.me授权过期提醒'''
    text = '''Hi，亲爱的%s，
    
感谢你使用thepast.me来整理自己的互联网印迹.
    
你在 %s 对thepast的授权过期了，影响到您的个人历史数据同步，

请依次访问下面的链接，重新授权：）

%s



如果你不愿意接收此类邮件，那么请到 http://thepast.me/settings 设置：）
---
http://thepast.me 
thanks''' % (u.name.encode("utf8"), ", ".join(names).encode("utf8"), "\n".join(reconnect_urls))

    print '--- send reconnections to %s %s' %(user_id, email)
    send_mail(["%s" % email], "thepast<help@thepast.me>", subject, text, "")


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
        try:
            send_today_in_history(uid)
        except:
            print traceback.format_exc()
        time.sleep(1)
        t += 1

