# -*- coding: utf-8 -*-

import hashlib
import urllib
import urlparse
from past import config
from past.utils.logger import logging
from past.utils.escape import json_decode
from past.utils import httplib2_request

from past.model.user import User, UserAlias, OAuth2Token
from past.model.data import RenrenUser
from past.model.data import (RenrenStatusData, RenrenFeedData, RenrenBlogData, 
    RenrenAlbumData, RenrenPhotoData)

from .oauth2 import OAuth2
from .error import OAuthError, OAuthLoginError, OAuthTokenExpiredError

log = logging.getLogger(__file__)

class Renren(OAuth2):

    authorize_uri = 'https://graph.renren.com/oauth/authorize'
    access_token_uri = 'https://graph.renren.com/oauth/token' 
    api_host = 'http://api.renren.com/restserver.do'

    def __init__(self, alias=None, access_token=None, refresh_token=None):
        d = config.APIKEY_DICT[config.OPENID_RENREN]
        super(Renren, self).__init__(provider = config.OPENID_RENREN,
            apikey = d["key"], 
            apikey_secret = d["secret"], 
            redirect_uri = d["redirect_uri"],
            scope = "read_user_status status_update read_user_feed publish_feed read_user_blog publish_blog read_user_photo photo_upload read_user_album",
            alias=alias, 
            access_token=access_token, 
            refresh_token=refresh_token)

    @classmethod                                                                   
    def get_client(cls, user_id):                                                  
        alias = UserAlias.get_by_user_and_type(user_id,                            
                config.OPENID_TYPE_DICT[config.OPENID_RENREN])                       
        if not alias:                                                              
            return None                                                            
                                                                                   
        token = OAuth2Token.get(alias.id)                                          
        if not token:                                                              
            return None                                                            
                                                                                   
        return cls(alias.alias, token.access_token, token.refresh_token)

    def _request(self, api, method="POST", extra_dict=None):
        if extra_dict is None:
            extra_dict = {}

        params = {
            "method": api,
            "v": "1.0",
            "access_token": self.access_token,
            "format": "json",
        }
        params.update(extra_dict)
        _, qs = Renren.sign(self.apikey_secret, **params)
        uri = "%s?%s" % (self.api_host, qs)

        log.info('getting %s...' % uri)
        resp, content = httplib2_request(uri, method)
        if resp.status == 200:
            user_id = self.user_alias and self.user_alias.user_id or None
            excp = OAuthTokenExpiredError(user_id=None,
                    openid_type=config.OPENID_TYPE_DICT[config.OPENID_RENREN], 
                    msg=content)
            jdata = json_decode(content) if content else None
            if jdata and isinstance(jdata, dict):
                error_code = jdata.get("error_code")
                error_msg = jdata.get("error_msg")
                if error_code:
                    if str(error_code) == "105":
                        ## 无效的token
                        excp.set_the_profile()
                        raise excp
                    elif str(error_code) == "106" and self.user_alias:
                        ## FIXME: 过期的token, 是不是106?
                        try:
                            new_tokens = super(Renren, self).refresh_tokens()
                            if new_tokens and isinstance(new_tokens, dict):
                                OAuth2Token.add(self.user_alias.id, 
                                        new_tokens.get("access_token"), 
                                        new_tokens.get("refresh_token"))
                                excp.clear_the_profile()
                        except OAuthError, e:
                            log.warn("refresh token fail: %s" % e)
                            excp.set_the_profile()
                            raise e
            return jdata

    def get_user_info(self, uid=None):
        qs = {
            "uid": uid or "",
            "fields": "uid,name,sex,star,zidou,vip,birthday,tinyurl,headurl,mainurl,hometown_location,work_history,university_history",
        }

        jdata = self._request("users.getInfo", "POST", qs)
        if jdata and isinstance(jdata, list) and len(jdata) >= 1:
            return RenrenUser(jdata[0])

    def get_timeline(self, page=1, count=100):
        d = {}
        d["count"] = count
        d["page"] = page

        contents = self._request("status.gets", "POST", d)
        ##debug
        if contents and isinstance(contents, list):
            print '---get renren status succ, result length is:', len(contents)
            return [RenrenStatusData(c) for c in contents]

    def get_feed(self, type_="10,20,30,40", page=1, count=50):
        d = {}
        d["count"] = count
        d["page"] = page
        d["type"] = type_

        contents = self._request("feed.get", "POST", d)
        ##debug
        if contents and isinstance(contents, list):
            print '---get renren feed succ, result length is:', len(contents)
            return [RenrenFeedData(c) for c in contents]

    def get_blogs(self, page=1, count=50):
        d = {}
        d["count"] = count
        d["page"] = page
        d["uid"] = self.alias

        contents = self._request("blog.gets", "POST", d)
        print '---get renren blog succ'
        if contents:
            return contents

    def get_blog(self, blog_id, uid):
        d = {}
        d["uid"] = uid or self.alias
        d["id"] = blog_id
        d["comment"] = 50

        contents = self._request("blog.get", "POST", d)
        if contents and isinstance(contents, dict):
            return RenrenBlogData(contents)

    def get_photos(self, aid, page=1, count=100):
        d = {}
        d["count"] = count
        d["page"] = page
        d["uid"] = self.alias
        d["aid"] = aid

        contents = self._request("photos.get", "POST", d)
        if contents and isinstance(contents, list):
            print '---get renren photos succ, result length is:', len(contents)
            return [RenrenPhotoData(c) for c in contents]
            
    def get_albums(self, page=1, count=1000):
        d = {}
        d["count"] = count
        d["page"] = page
        d["uid"] = self.alias

        contents = self._request("photos.getAlbums", "POST", d)
        if contents and isinstance(contents, list):
            print '---get renren album succ, result length is:', len(contents)
            return [RenrenAlbumData(c) for c in contents]

    @classmethod
    def sign(cls, token_secret, **kw):
        
        d = {}
        for k, v in kw.items():
            d[k] = v
        d_ = sorted(d.items(), key=lambda x:x[0])

        dd_ = ["%s=%s" %(x[0], x[1]) for x in d_]
        raw = "%s%s" %("".join(dd_), token_secret)
        hashed = hashlib.md5(raw).hexdigest()

        d["sig"] = hashed
        
        qs = urllib.urlencode(d_).replace("+", "%20")
        qs += "&" + urllib.urlencode({"sig":hashed})

        return (d, qs)
