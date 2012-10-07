# -*- coding: utf-8 -*-

import urllib
from past import config
from past.model.user import UserAlias
from past.utils.escape import json_decode
from past.utils import httplib2_request

from .error import OAuthLoginError

class OAuth2(object):

    authorize_uri = ''
    access_token_uri = ''
    api_host = ''
    
    def __init__(self, provider=None, apikey=None, apikey_secret=None, redirect_uri=None, 
            scope=None, state=None, display=None, 
            alias=None, access_token=None, refresh_token=None):

        self.provider = provider
        self.apikey = apikey
        self.apikey_secret = apikey_secret
        self.redirect_uri = redirect_uri

        self.scope = scope
        self.state = state
        self.display = display

        self.alias = alias
        if alias:
            self.user_alias = UserAlias.get(
                    config.OPENID_TYPE_DICT[provider], alias)
        else:
            self.user_alias = None
        self.access_token = access_token
        self.refresh_token = refresh_token

    def __repr__(self):
        return '<provider=%s, alias=%s, access_token=%s, refresh_token=%s, \
                api_host=%s>' % (self.provider, self.alias, self.access_token, 
                self.refresh_token, self.api_host)
    __str__ = __repr__

    def login(self):
        qs = {
            'client_id'     : self.apikey,
            'response_type' : 'code',
            'redirect_uri'  : self.redirect_uri,
        }
        if self.display:
            qs['display'] = self.display
        if self.scope:
            qs['scope'] = self.scope
        if self.state:
            qs['state'] = self.state
            
        qs = urllib.urlencode(qs)
        uri = '%s?%s' %(self.authorize_uri, qs)

        return uri

    def get_access_token(self, authorization_code):
        qs = {
            "client_id": self.apikey,
            "client_secret": self.apikey_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
            "code": authorization_code,
        }
        qs = urllib.urlencode(qs)
        resp, content = httplib2_request(self.access_token_uri, "POST", body=qs)
        excp = OAuthLoginError(msg='get_access_token, status=%s,reason=%s,content=%s' \
                %(resp.status, resp.reason, content))
        if resp.status != 200:
            raise excp

        jdata = json_decode(content) if content else None
        return jdata
        

    def refresh_tokens(self):
        qs = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.apikey,
            "client_secret": self.apikey_secret,
            "redirect_uri": self.redirect_uri,
        }
        resp, content = httplib2_request(self.access_token_uri, "POST", 
            body=urllib.urlencode(qs))
        excp = OAuthLoginError(self.user_alias.user_id, self.provider, 
                'refresh_tokens, status=%s,reason=%s,content=%s' \
                %(resp.status, resp.reason, content))
        if resp.status != 200:
            raise excp

        jdata = json_decode(content) if content else None
        return jdata

    def set_token(self, access_token, refresh_token):
        self.access_token = access_token
        self.refresh_token = refresh_token

    def get_user_info(self, uid):
        raise NotImplementedError

