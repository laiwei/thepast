# -*- coding: utf-8 -*-
import time
import hashlib
import urllib
import hmac
import binascii
import urlparse
from past import config
from past.utils import randbytes
from past.utils.logger import logging
from past.utils.escape import json_decode, json_encode
from past.utils import httplib2_request

from past.model.user import User, UserAlias, OAuth2Token
from past.model.data import QQWeiboUser
from past.model.data import QQWeiboStatusData

from .error import OAuthError, OAuthLoginError, OAuthTokenExpiredError

log = logging.getLogger(__file__)

##腾讯微博使用的是Oauth1.0授权
class QQWeibo(object):
    provider = config.OPENID_QQ

    request_token_uri = "https://open.t.qq.com/cgi-bin/request_token"
    authorize_uri = "https://open.t.qq.com/cgi-bin/authorize"
    access_token_uri = "https://open.t.qq.com/cgi-bin/access_token"
    api_uri = "http://open.t.qq.com/api"

    def __init__(self, alias=None, 
            apikey=None, apikey_secret=None, redirect_uri=None, 
            token=None, token_secret=None, openid=None, openkey=None):

        self.consumer_key = apikey or config.APIKEY_DICT[config.OPENID_QQ]['key']
        self.consumer_secret = apikey_secret or config.APIKEY_DICT[config.OPENID_QQ]['secret']
        self.callback = redirect_uri or config.APIKEY_DICT[config.OPENID_QQ]['redirect_uri']

        self.token = token
        self.token_secret = token_secret
        #XXX:no use?
        self.openid = openid
        self.openkey = openkey

        self.alias=alias
        if alias:
            self.user_alias = UserAlias.get(
                    config.OPENID_TYPE_DICT[config.OPENID_QQ], alias)
        else:
            self.user_alias = None

    def __repr__(self):
        return "<QQWeibo consumer_key=%s, consumer_secret=%s, token=%s, token_secret=%s>" \
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
            r = self.GET(uri, {'oauth_callback':self.callback})
            qs = urlparse.parse_qs(r)
            self.set_token(qs.get('oauth_token')[0], qs.get('oauth_token_secret')[0])

            return (self.token, self.token_secret)
        except OAuthError, e:
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
    def login(self):
        self.get_request_token()
        return self.authorize_token()
    
    ##get access_token use authorized_code
    def get_access_token(self, oauth_verifier):
        uri = self.__class__.access_token_uri
        qs = {
            "oauth_token": self.token,
            "oauth_verifier": oauth_verifier,
        }
        
        r = self.GET(uri, qs)
        d = urlparse.parse_qs(r)
        self.token = d['oauth_token'][0]
        self.token_secret = d['oauth_token_secret'][0]

        return (self.token, self.token_secret)

    @classmethod                                                                   
    def get_client(cls, user_id):                                                  
        alias = UserAlias.get_by_user_and_type(user_id,                            
                config.OPENID_TYPE_DICT[config.OPENID_QQ])                       
        if not alias:                                                              
            return None                                                            

        token = OAuth2Token.get(alias.id)
        if not token:
            return None
                                                                                   
        return cls(alias=alias.alias, token=token.access_token, token_secret=token.refresh_token)
    
    def get_user_info(self):
        jdata = self.access_resource2("GET", "/user/info", {"format":"json"})
        if jdata and isinstance(jdata, dict):
            return QQWeiboUser(jdata)

    ##使用access_token访问受保护资源，该方法中会自动传递oauth_token参数
    ##params为dict，是需要传递的参数, body 和 headers不加入签名
    def access_resource(self, method, api, params, file_params=None):
        uri = self.__class__.api_uri + api

        if params:
            params['oauth_token'] = self.token
        else:
            params = {'oauth2_token':self.token,}
        log.info("accesss qq resource: %s, %s" %(uri, params))
        if method == "GET":
            return self.GET(uri, params)
        if method == "POST":
            return self.POST(uri, params, file_params)

    def GET(self, uri, params):
        return self._request("GET", uri, params, None)

    def POST(self, uri, params, file_params):
        return self._request("POST", uri, params, file_params)

    def _request(self, method, uri, kw, file_params):
        raw_qs, qs = QQWeibo.sign(method, uri, self.consumer_key, 
                self.consumer_secret, self.token_secret, **kw)
        if method == "GET":
            full_uri = "%s?%s" % (uri, qs)
            resp, content = httplib2_request(full_uri, method)
        else:
            if file_params:
                from past.utils import encode_multipart_data
                body, headers = encode_multipart_data(raw_qs, file_params)
            else:
                body = qs
                headers = None
            resp, content = httplib2_request(uri, method, body, headers=headers)
            
        log.debug("---qq check result, status: %s, resp: %s, content: %s" %(resp.status, resp, content))
        if resp.status != 200:
            raise OAuthLoginError(msg='get_unauthorized_request_token fail, status=%s:reason=%s:content=%s' \
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

        dd_ = [urllib.urlencode([x]).replace("+", "%20") for x in d_]
        part3 = urllib.quote("&".join(dd_))
        
        key = consumer_secret + "&"
        if token_secret:
            key += token_secret

        raw = "%s&%s&%s" % (part1, part2, part3)
        
        if d['oauth_signature_method'] != "HMAC-SHA1":
            raise

        hashed = hmac.new(key, raw, hashlib.sha1)
        hashed = binascii.b2a_base64(hashed.digest())[:-1]
        d["oauth_signature"] = hashed
        
        qs = urllib.urlencode(d_).replace("+", "%20")
        qs += "&" + urllib.urlencode({"oauth_signature":hashed})

        return (d, qs)

    def access_resource2(self, method, api, params, file_params=None):
        r = self.access_resource(method, api, params, file_params)
        if not r:
            return None
        try:
            jdata = json_decode(r)
        except:
            ##XXX:因为腾讯的json数据很2，导致有时候decode的时候会失败，一般都是因为双引号没有转义的问题
            import re
            r_ = re.sub('=\\"[^ >]*"( |>)', '', r)
            try:
                jdata = json_decode(r_)
            except Exception, e:
                log.warning("json_decode qqweibo data fail, %s" % e)
                return None
        if jdata and isinstance(jdata, dict):
            ret_code = jdata.get("ret")
            msg = jdata.get("msg")
            user_id = self.user_alias and self.user_alias.user_id or None
            excp = OAuthTokenExpiredError(user_id,
                    config.OPENID_TYPE_DICT[config.OPENID_QQ], msg)
            if str(ret_code) == "0":
                excp.clear_the_profile()
                data = jdata.get("data")
                return data
            elif str(ret_code) == "3":
                excp.set_the_profile()
                raise excp
            else:
                log.warning("access qqweibo resource %s fail, ret_code=%s, msg=%s" %(api, ret_code, msg))

    def get_old_timeline(self, pagetime, reqnum=200):
        return self.get_timeline(reqnum=reqnum, pageflag=1, pagetime=pagetime)

    def get_new_timeline(self, reqnum=20):
        return self.get_timeline(reqnum=reqnum)

    def get_timeline(self, format_="json", reqnum=200, type_=0, contenttype=0, pagetime=0, pageflag=0):
        qs = {}
        qs['format'] = format_
        qs['reqnum'] = reqnum
        qs['type'] = type_
        qs['contenttype'] = contenttype

        #pageflag: 分页标识（0：第一页，1：向下翻页，2：向上翻页）
        #lastid: 和pagetime配合使用（第一页：填0，向上翻页：填上一次请求返回的第一条记录id，向下翻页：填上一次请求返回的最后一条记录id）
        #pagetime 本页起始时间（第一页：填0，向上翻页：填上一次请求返回的第一条记录时间，向下翻页：填上一次请求返回的最后一条记录时间）
        qs['pageflag'] = pageflag
        qs['pagetime'] = pagetime if pagetime is not None else 0

        jdata = self.access_resource2("GET", "/statuses/broadcast_timeline", qs)
        if jdata and isinstance(jdata, dict):
            info = jdata.get("info") or []
            print '---status from qqweibo, len is: %s' % len(info)
            return [QQWeiboStatusData(c) for c in info]

    def post_status(self, text):
        from flask import request
        qs = {"content": text, "format": "json", "clientip": request.remote_addr,}
        return self.access_resource2("POST", "/t/add", qs)

    def post_status_with_image(self, text, image_file):
        from flask import request
        qs = {"content": text, "format": "json", "clientip": request.remote_addr,}
        f = {"pic" : image_file}
        return self.access_resource2("POST", "/t/add_pic", qs, f)

