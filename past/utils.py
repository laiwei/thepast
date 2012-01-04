#-*- coding:utf-8 -*-
import os
import httplib2
from base64 import b64encode

def randbytes(bytes_):
    return b64encode(os.urandom(bytes_)).rstrip('=')

def httplib2_request(uri, method="GET", body='', headers=None, 
        redirections=httplib2.DEFAULT_MAX_REDIRECTS, 
        connection_type=None):

    DEFAULT_POST_CONTENT_TYPE = 'application/x-www-form-urlencoded'

    if not isinstance(headers, dict):
        headers = {}

    if method == "POST":
        headers['Content-Type'] = headers.get('Content-Type', 
            DEFAULT_POST_CONTENT_TYPE)

    return httplib2.Http().request(uri, method=method, body=body,
        headers=headers, redirections=redirections,
        connection_type=connection_type)

