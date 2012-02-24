# -*- coding: utf-8 -*-

import time
import urllib
import urlparse
import hashlib
import hmac
import binascii

import tweepy
from tweepy.error import TweepError

import config
from past.utils.escape import json_encode, json_decode
from past.utils import randbytes
from past.utils import httplib2_request
from past.model.data import SinaWeiboUser, DoubanUser, TwitterUser, QQWeiboUser

class OAuthLoginError(Exception):
    def __init__(self, msg):
        if isinstance(msg, TweepError):
            self.msg = "%s:%s" %(msg.reason, msg.response) 
        else:
            self.msg = msg

    def __str__(self):
        return "%s" % (self.msg,)
    __repr__ = __str__

class TwitterOAuthLogin(object):
    provider = config.OPENID_TWITTER

    def __init__(self, apikey, apikey_secret, redirect_uri):
        self.consumer_key = apikey
        self.consumer_secret = apikey_secret
        self.callback = redirect_uri
        self.auth = self._get_auth()

    def _get_auth(self):
        return tweepy.OAuthHandler(self.consumer_key, self.consumer_secret, self.callback)

    def get_login_uri(self):
        return self.auth.get_authorization_url()

    def get_access_token(self, verifier=None):
        self.auth.get_access_token(verifier)
        print self.auth.access_token.key
        t = {"access_token":self.auth.access_token.key, 
            "access_token_secret": self.auth.access_token.secret,}
        return t
    
    def save_request_token_to_session(self, session_):
        t = {"key": self.auth.request_token.key,
            "secret": self.auth.request_token.secret,}
        session_['request_token'] = json_encode(t)

    def get_request_token_from_session(self, session_, delete=True):
        t = session_.get("request_token")
        token = json_decode(t) if t else {}
        if delete:
            self.delete_request_token_from_session(session_)
        return token

    def delete_request_token_from_session(self, session_):
        session_.pop("request_token", None)

    def api(self, access_token=None, access_token_secret=None):
        if access_token and access_token_secret:
            self.auth.set_access_token(access_token, access_token_secret)

        return tweepy.API(self.auth, parser=tweepy.parsers.JSONParser())

    def get_user_info(self, api):
        user = api.me()
        return TwitterUser(user)

class OAuth2Login(object):
    version = '2.0'

    authorize_uri       = ''
    access_token_uri    = ''
    
    def __init__(self, apikey, apikey_secret, redirect_uri, 
            scope=None, state=None, display=None):

        self.apikey = apikey
        self.apikey_secret = apikey_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.state = state
        self.display = display

    def get_login_uri(self):
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
        print '--------resp, content', content, type(content)
        if resp.status != 200:
            raise OAuthLoginError('get_access_token, status=%s:reason=%s:content=%s' \
                    %(resp.status, resp.reason, content))
        return json_decode(content)

class DoubanLogin(OAuth2Login):
    provider = config.OPENID_DOUBAN   

    authorize_uri = 'https://www.douban.com/service/auth2/auth'
    access_token_uri = 'https://www.douban.com/service/auth2/token' 
    user_info_uri = 'https://api.douban.com/people/@me'

    def __init__(self, apikey, apikey_secret, redirect_uri, 
            scope=None, state=None, display=None):
        super(DoubanLogin, self).__init__(apikey, apikey_secret, redirect_uri, scope)

    def get_user_info(self, access_token, uid=None):
        headers = {"Authorization": "Bearer %s" % access_token}     
        qs = {
            "alt":"json",
        }
        uri = "%s?%s" %(self.user_info_uri, urllib.urlencode(qs))
        resp, content = httplib2_request(uri, "GET", 
                headers = headers)
        print '--------resp, content', content, type(content)
        if resp.status != 200:
            raise OAuthLoginError('get_access_token, status=%s:reason=%s:content=%s' \
                    %(resp.status, resp.reason, content))
        r = json_decode(content)
        user_info = DoubanUser(r)

        return user_info
        
class SinaLogin(OAuth2Login):
    provider = config.OPENID_SINA

    authorize_uri = 'https://api.weibo.com/oauth2/authorize'
    access_token_uri = 'https://api.weibo.com/oauth2/access_token' 
    user_info_uri = 'https://api.weibo.com/2/users/show.json' 

    def __init__(self, apikey, apikey_secret, redirect_uri):
        super(SinaLogin, self).__init__(apikey, apikey_secret, redirect_uri)

    def get_user_info(self, access_token, uid):
        qs = {
            "source": self.apikey,
            "access_token": access_token,
            "uid": uid,
        }
        qs = urllib.urlencode(qs)
        uri = "%s?%s" % (self.user_info_uri, qs)
        resp, content = httplib2_request(uri, "GET")
        print '--------resp, content', content, type(content)
        if resp.status != 200:
            raise OAuthLoginError('get_access_token, status=%s:reason=%s:content=%s' \
                    %(resp.status, resp.reason, content))
        r = json_decode(content)
        user = SinaWeiboUser(r)

        return user

##腾讯微博使用的是Oauth1.0授权
class QQOAuth1Login(object):
    provider = config.OPENID_QQ

    request_token_uri = "https://open.t.qq.com/cgi-bin/request_token"
    authorize_uri = "https://open.t.qq.com/cgi-bin/authorize"
    access_token_uri = "https://open.t.qq.com/cgi-bin/access_token"
    api_uri = "http://open.t.qq.com/api"

    def __init__(self, apikey=None, apikey_secret=None, redirect_uri=None, 
            token=None, token_secret=None, openid=None, openkey=None):

        self.consumer_key = apikey or config.APIKEY_DICT[config.OPENID_QQ]['key']
        self.consumer_secret = apikey_secret or config.APIKEY_DICT[config.OPENID_QQ]['secret']
        self.callback = redirect_uri or config.APIKEY_DICT[config.OPENID_QQ]['redirect_uri']

        self.token = token
        self.token_secret = token_secret
        self.openid = openid
        self.openkey = openkey

    def __repr__(self):
        return "<QQOAuth1Login consumer_key=%s, consumer_secret=%s, token=%s, token_secret=%s>" \
            % (self.consumer_key, self.consumer_secret, self.token, self.token_secret)
    __str__ = __repr__

    def save_request_token_to_session(self, session_):
        t = {"key": self.token,
            "secret": self.token_secret,}
        session_['request_token'] = json_encode(t)

    def get_request_token_from_session(self, session_, delete=True):
        t = session_.get("request_token")
        token = json_decode(t) if t else {}
        if delete:
            self.delete_request_token_from_session(session_)
        return token

    def delete_request_token_from_session(self, session_):
        session_.pop("request_token", None)

    def set_token(self, token, token_secret):
        self.token = token
        self.token_secret = token_secret

    ##get unauthorized request_token
    def get_request_token(self):
        ##返回结果
        ##oauth_token=9bae21d3bbe2407da94a4c4e4355cfcb&oauth_token_secret=128b87904122d43cde6b02962d8eeea6&oauth_callback_confirmed=true
        uri = self.__class__.request_token_uri
        try:
            r = self.GET(uri, oauth_callback=self.callback)
            qs = urlparse.parse_qs(r)
            self.set_token(qs.get('oauth_token')[0], qs.get('oauth_token_secret')[0])

            return (self.token, self.token_secret)
        except OAuthLoginError, e:
            print e
        except AttributeError, e:
            print e
            
    ##authorize the request_token
    def authorize_token(self):
        ##用户授权之后会返回如下结果
        ##http://thepast.me/connect/qq/callback
        ##?oauth_token=xxx&oauth_verifier=468092&openid=xxx&openkey=xxx
        uri = "%s?oauth_token=%s" % (self.__class__.authorize_uri, self.token)
        return uri
    
    ## 为了和其他几个接口保持一致
    def get_login_uri(self):
        self.get_request_token()
        return self.authorize_token()
    
    ##get access_token use authorized_code
    def get_access_token(self, oauth_verifier):
        uri = self.__class__.access_token_uri
        qs = {
            "oauth_token": self.token,
            "oauth_verifier": oauth_verifier,
        }
        
        r = self.GET(uri, **qs)
        print "access_token:", r
        d = urlparse.parse_qs(r)
        self.token = d['oauth_token'][0]
        self.token_secret = d['oauth_token_secret'][0]

        return (self.token, self.token_secret)

    #TODO:这个应当移动到api_client相应的地方
    def get_user_info(self):
        #uri = self.__class__.api_uri + "/user/info"
        #r = self.GET(uri, format="json", oauth_token=self.token)
        r = self.access_resource("GET", "/user/info", {"format":"json"})
        print "--------user info:",r 
        r = json_decode(r) if r else {}
        return QQWeiboUser(r.get('data'))

    ##使用access_token访问受保护资源，该方法中会自动传递oauth_token参数
    ##params为dict，是需要传递的参数
    def access_resource(self, method, api, params=None):
        uri = self.__class__.api_uri + api

        if method == "GET":
            return self.GET(uri, oauth_token=self.token, **params)
        if method == "POST":
            return self.POST(uri, oauth_token=self.token, **params)

    def GET(self, uri, **kw):
        return self._request("GET", uri, **kw)

    def POST(self, uri, **kw):
        return self._request("POST", uri, **kw)

    def DELETE(self):
        raise NotImplementedError

    def PUT(self):
        raise NotImplementedError

    def _request(self, method, uri, **kw):
        signature, qs = QQOAuth1Login.sign(method, uri, self.consumer_key, 
                self.consumer_secret, self.token_secret, **kw)
        if method == "GET":
            full_uri = "%s?%s" % (uri, qs)
            print '--------get uri:', full_uri
            resp, content = httplib2_request(full_uri, method)
        else:
            resp, content = httplib2_request(uri, method, qs)
            
        if resp.status != 200:
            raise OAuthLoginError('get_unauthorized_request_token fail, status=%s:reason=%s:content=%s' \
                    %(resp.status, resp.reason, content))

        return content
        
    @classmethod
    def sign(cls, method, uri, consumer_key, consumer_secret, token_secret, **kw):
        
        part1 = method.upper()
        part2 = urllib.quote(uri.lower(), safe="")
        part3 = ""
        
        d = {}
        for k, v in kw.items():
            d[k] = v

        d['oauth_consumer_key'] = consumer_key

        if 'oauth_timestamp' not in d or not d['oauth_timestamp']:
            d['oauth_timestamp'] = str(int(time.time()))

        if 'oauth_nonce' not in d or not d['oauth_nonce']:
            d['oauth_nonce'] = randbytes(32)

        if 'oauth_signature_method' not in d or not d['oauth_signature_method']:
            d['oauth_signature_method'] = 'HMAC-SHA1'

        if 'oauth_version' not in d or not d['oauth_version']:
            d['oauth_version'] = '1.0'

        d_ = sorted(d.items(), key=lambda x:x[0])

        dd_ = [urllib.urlencode([x]) for x in d_]
        part3 = urllib.quote("&".join(dd_))
        print '--------------d_:', d_
        
        key = consumer_secret + "&"
        if token_secret:
            key += token_secret
        print '------key:', key

        raw = "%s&%s&%s" % (part1, part2, part3)
        print '----------raw:', raw
        
        if d['oauth_signature_method'] != "HMAC-SHA1":
            raise

        hashed = hmac.new(key, raw, hashlib.sha1)
        hashed = binascii.b2a_base64(hashed.digest())[:-1]
        
        qs = urllib.urlencode(d_)
        qs += "&" + urllib.urlencode({"oauth_signature":hashed})

        print '-------------qs:', qs

        return (hashed, qs)

