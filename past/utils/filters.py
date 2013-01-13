#!-*- coding:utf8 -*-
import re
from datetime import datetime, timedelta
from past.utils import escape

_paragraph_re = re.compile(r'(?:\r\n|\r|\n)')

def nl2br(value):
    result = u"<br/>\n".join(_paragraph_re.split(value))
    return result

def linkify(text):
    return escape.linkify(text)

def html_parse(s, preserve):
    return escape.MyHTMLParser.parse(text, preserve)

def stream_time(d):
    now = datetime.now()
    delta = now -d
    
    #duration = delta.total_seconds()  ##python2.7
    duration = delta.days * 365 * 86400 + delta.seconds
    if duration < 0:
        return u'穿越了...'
    elif duration <= 60:
        return u'%s秒前' %int(duration)
    elif duration <= 3600:
        return u'%s分钟前' %int(duration/60)
    elif duration <= 3600*12:
        return u'%s小时前' %int(duration/3600)
    elif d.year==now.year and d.month==now.month and d.day == now.day:
        return u'今天 %s' %d.strftime("%H:%M")
    elif d.year==now.year and d.month==now.month and d.day + 1 == now.day:
        return u'昨天 %s' %d.strftime("%H:%M")
    elif d.year==now.year and d.month==now.month and d.day + 2 == now.day:
        return u'前天 %s' %d.strftime("%H:%M")
    elif d.year == now.year:
        return u'今年 %s' %d.strftime("%m-%d %H:%M")
    elif d.year + 1 == now.year:
        return u'去年 %s' %d.strftime("%m-%d %H:%M")
    elif d.year + 2 == now.year:
        return u'前年 %s' %d.strftime("%m-%d %H:%M")
    elif d.year + 3 == now.year:
        return u'三年前 %s' %d.strftime("%m-%d %H:%M")
    elif d.year + 4 == now.year:
        return u'四年前 %s' %d.strftime("%m-%d %H:%M")
    elif d.year + 5 == now.year:
        return u'五年前 %s' %d.strftime("%m-%d %H:%M")
    elif d.year + 6 == now.year:
        return u'六年前 %s' %d.strftime("%m-%d %H:%M")
    else:
        return d.strftime("%Y-%m-%d %H:%M:%S")
    
