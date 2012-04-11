#-*- coding:utf-8 -*-

import os
import datetime
import hashlib
import urlparse
import httplib2
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from past import app
from past.model.user import User
from past.model.status import Status
from past.utils import wrap_long_line, filters, randbytes
from past import config

def generate_pdf(filename, uid, start, count, cate=None, with_head=True, capacity=50*1024):

    #########Set FONT################
    from xhtml2pdf.default import DEFAULT_FONT
    from xhtml2pdf.document import pisaDocument
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    pdfmetrics.registerFont(TTFont('zhfont', os.path.join(app.root_path, 'static/font/yahei-consolas.ttf')))
    DEFAULT_FONT["helvetica"] = "zhfont"
    css = open(os.path.join(app.root_path, "static/css/pdf.css")).read()

    #result = StringIO.StringIO()
    full_file_name = get_pdf_full_filename(filename)
    if not full_file_name:
        return None
    result = open(full_file_name, 'wb', 1024*1000)

    user = User.get(uid)
    if not user:
        return None

    # get status
    ids = Status.get_ids(user_id=uid, start=start, limit=count, cate=cate)
    status_list = Status.gets(ids)
    _html = render(user, status_list, with_head)
    _pdf = pisaDocument(_html, result, default_css=css, link_callback=link_callback, capacity=capacity)
    result.close()

    if not _pdf.err:
        return full_file_name
    else:
        return None

def render(user, status_list, with_head=True):
    if with_head:
        _html = u"""<html> <body>
            <div id="Top">
                <img src="%s"/> &nbsp; &nbsp;&nbsp; The Past of Me | 个人杂志计划&nbsp;&nbsp;&nbsp;%s&nbsp;&nbsp;&nbsp;CopyRight©%s
                <br/>
            </div>
            <br/> <br/>

            <div class="box">
        """ % (os.path.join(app.root_path, "static/img/logo.png"), 
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user.name)
    else:
        _html = u"""<html> <body><div class="box">"""

    from jinja2 import Environment, PackageLoader
    env = Environment(loader=PackageLoader('past', 'templates'))
    env.filters['wrap_long_line'] = wrap_long_line
    env.filters['nl2br'] = filters.nl2br
    t = env.get_template('status.html')
    m = t.module
    for s in status_list:
        if not s:
            continue
        if s.category == config.CATE_DOUBAN_STATUS:
            r = m.douban_status(s, pdf=True)
        elif s.category == config.CATE_SINA_STATUS:
            r = m.sina_status(s, pdf=True)
        elif s.category == config.CATE_TWITTER_STATUS:
            r = m.twitter_status(s, pdf=True)
        elif s.category == config.CATE_QQWEIBO_STATUS:
            r = m.qq_weibo_status(s, pdf=True)
        else:
            r = ''
        if not r:
            continue
        _html += '''<div class="cell">''' + r + '''</div>'''
        s._clear_cache(user_id = s.user_id, status_id = s.id)
    _html += """</div></body></html>"""
    return _html

def link_callback(uri, rel):
    lower_uri = uri.lower()
    print '%s getting %s' % (datetime.datetime.now(), lower_uri)
    if not (lower_uri.startswith('http://') or 
            lower_uri.startswith('https://') or lower_uri.startswith('ftp://')):
        return uri

    d = hashlib.md5()
    d.update(uri)
    d = d.hexdigest()
    _sub_dir = '%s/%s' % (config.CACHE_DIR, d[:2])

    if not os.path.isdir(_sub_dir):
        os.makedirs(_sub_dir)
    if not (os.path.exists(_sub_dir) and os.path.isdir(_sub_dir)):
        return uri

    _filename = d[0:8] + os.path.basename(urlparse.urlsplit(uri).path)
    cache_file = os.path.join(_sub_dir, _filename)

    if os.path.exists(cache_file) and os.path.getsize(cache_file) > 0:
        return cache_file
    
    resp, content = httplib2.Http().request(uri)
    if resp.status == 200:
        with open(cache_file, 'w') as f:
            f.write(content)
        return cache_file
    else:
        print 'get %s fail, status_code is %s, so return none' % (uri,resp.status)
        return ''

    return uri

def get_pdf_filename(uid):
    return "thepast.me_%s.pdf" % uid

def get_pdf_full_filename(filename):
    pdf_file_dir = config.PDF_FILE_DOWNLOAD_DIR

    if not os.path.isdir(pdf_file_dir):
        os.makedirs(pdf_file_dir)
    if not os.path.isdir(pdf_file_dir):
        return False

    return os.path.join(config.PDF_FILE_DOWNLOAD_DIR, filename)

def is_pdf_file_exists(filename):
    full_file_name = get_pdf_full_filename(filename)
    if os.path.exists(full_file_name) and os.path.getsize(full_file_name) > 0:
        return True
    return False

def is_user_pdf_file_exists(uid):
    f = get_pdf_filename(uid)
    return is_pdf_file_exists(f)
