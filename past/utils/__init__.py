#-*- coding:utf-8 -*-
import os
import httplib2
import hashlib
import urlparse
from base64 import b64encode
from past import config

def randbytes(bytes_):
    return b64encode(os.urandom(bytes_)).rstrip('=')

def httplib2_request(uri, method="GET", body='', headers=None, 
        redirections=httplib2.DEFAULT_MAX_REDIRECTS, 
        connection_type=None, disable_ssl_certificate_validation=True):

    DEFAULT_POST_CONTENT_TYPE = 'application/x-www-form-urlencoded'

    if not isinstance(headers, dict):
        headers = {}

    if method == "POST":
        headers['Content-Type'] = headers.get('Content-Type', 
            DEFAULT_POST_CONTENT_TYPE)

    return httplib2.Http(disable_ssl_certificate_validation=disable_ssl_certificate_validation).\
        request(uri, method=method, body=body,
        headers=headers, redirections=redirections,
        connection_type=connection_type)

def link_callback(uri, rel):
    lower_uri = uri.lower()
    if not (lower_uri.startswith('http://') or 
            lower_uri.startswith('https://') or lower_uri.startswith('ftp://')):
        return uri

    d = hashlib.md5()
    d.update(uri)
    d = d.hexdigest()
    _sub_dir = '%s/%s' %(config.CACHE_DIR, d[:2])

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
        open(cache_file, 'w').write(content)
        return cache_file

    return uri

def wrap_long_line(text, max_len=60):
    if len(text) <= max_len:
        return text

    out_text = ""
    times = len(text)*1.0 / max_len
    if times > int(times):
        times = int(times) + 1
    else:
        times = int(times)

    i = 0
    index = 0
    while i < times:
        out_text += text[index:index+max_len] + "\n"
        index += max_len
        i += 1

    return out_text

