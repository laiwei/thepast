# -*- coding: utf-8 -*-

import urllib
import urlparse
from past import config
from past.utils.logger import logging
from past.utils.escape import json_decode
from past.utils import httplib2_request

from past.model.user import User, UserAlias, OAuth2Token
from past.model.data import DoubanUser
from past.model.data import DoubanNoteData, DoubanStatusData, DoubanMiniBlogData

from .oauth2 import OAuth2
from .error import OAuthError, OAuthLoginError, OAuthTokenExpiredError

log = logging.getLogger(__file__)

class Douban(OAuth2):

    authorize_uri = 'https://www.douban.com/service/auth2/auth'
    access_token_uri = 'https://www.douban.com/service/auth2/token' 
    api_host = "https://api.douban.com"

    def __init__(self, alias=None, access_token=None, refresh_token=None):
        d = config.APIKEY_DICT[config.OPENID_DOUBAN]
        super(Douban, self).__init__(provider = config.OPENID_DOUBAN, 
                apikey = d["key"], 
                apikey_secret = d["secret"], 
                redirect_uri = d["redirect_uri"],
                alias=alias, 
                access_token=access_token, 
                refresh_token=refresh_token)

    @classmethod
    def get_client(cls, user_id):
        alias = UserAlias.get_by_user_and_type(user_id, 
                config.OPENID_TYPE_DICT[config.OPENID_DOUBAN])
        if not alias:
            return None

        token = OAuth2Token.get(alias.id)
        if not token:
            return None

        return cls(alias.alias, token.access_token, token.refresh_token)

    def check_result(self, uri, resp, content):
        user_id = self.user_alias and self.user_alias.user_id or None
        excp = OAuthTokenExpiredError(user_id,
                config.OPENID_TYPE_DICT[config.OPENID_DOUBAN], content)
        jdata = json_decode(content) if content else None
        if str(resp.status) == "200":
            excp.clear_the_profile()
            return jdata

        log.warning("get %s fail, status code=%s, msg=%s. go to refresh token" \
            % (uri, resp.status, content))
        if jdata and isinstance(jdata, dict):
            error_code = jdata.get("code") 
            if str(error_code) == "103" or str(error_code) == "123":
                excp.set_the_profile()
                raise excp
            elif str(error_code) == "106" and self.user_alias:
                try:
                    new_tokens = super(Douban, self).refresh_tokens()
                    if new_tokens and isinstance(new_tokens, dict):
                        OAuth2Token.add(self.user_alias.id, 
                                new_tokens.get("access_token"), 
                                new_tokens.get("refresh_token"))
                        excp.clear_the_profile()
                except OAuthError, e:
                    log.warn("refresh token fail: %s" % e)
                    excp.set_the_profile()
                    raise e

    def get(self, url, extra_dict=None):
        uri = urlparse.urljoin(self.api_host, url)
        if extra_dict is None:
            extra_dict = {}
        extra_dict["alt"] = "json"

        if extra_dict:
            qs = urllib.urlencode(extra_dict)
            if "?" in uri:
                uri = "%s&%s" % (uri, qs)
            else:
                uri = "%s?%s" % (uri, qs)
        headers = {"Authorization": "Bearer %s" % self.access_token}     
        log.info('getting %s...' % uri)

        resp, content = httplib2_request(uri, "GET", headers=headers)
        return self.check_result(uri, resp, content)

    def post(self, url, body, headers=None):
        uri = urlparse.urljoin(self.api_host, url)
        if headers is not None:
            headers.update({"Authorization": "Bearer %s" % self.access_token})
        else:
            headers = {"Authorization": "Bearer %s" % self.access_token}     

        resp, content = httplib2_request(uri, "POST", body=body, headers=headers)
        return self.check_result(uri, resp, content)


    def get_user_info(self, uid="@me"):
        uid = uid or "@me"
        api = "/people/%s" % uid
        jdata = self.get(api)
        if jdata and isinstance(jdata, dict):
            return DoubanUser(jdata)

    def get_me2(self):
        return self.get("/shuo/users/%s" % self.alias)

    def get_note(self, note_id):
        return self.get("/note/%s" % note_id)

    def get_timeline(self, since_id=None, until_id=None, count=200, user_id=None):
        user_id = user_id or self.alias
        qs = {}
        qs['count'] = count
        if since_id is not None:
            qs['since_id'] = since_id
        if until_id is not None:
            qs['until_id'] = until_id
        qs = urllib.urlencode(qs)
        jdata = self.get("/shuo/v2/statuses/user_timeline/%s?%s" % (user_id, qs))
        if jdata and isinstance(jdata, list):
            return [DoubanStatusData(c) for c in jdata]

    def get_home_timeline(self, since_id=None, until_id=None, count=200):
        qs = {}
        qs['count'] = count
        if since_id is not None:
            qs['since_id'] = since_id
        if until_id is not None:
            qs['until_id'] = until_id
        qs = urllib.urlencode(qs)
        jdata = self.get("/shuo/v2/statuses/home_timeline?%s" % qs)
        if jdata and isinstance(jdata, list):
            return [DoubanStatusData(c) for c in jdata]

    # 发广播，只限文本
    def post_status(self, text, attach=None):
        qs = {}
        qs["text"] = text
        if attach is not None:
            qs["attachments"] = attach
        qs = urllib.urlencode(qs)
        return self.post("/shuo/statuses/", body=qs)

    def post_status_with_image(self, text, image_file):
        from past.utils import encode_multipart_data
        d = {"text": text}
        f = {"image" : image_file}
        body, headers = encode_multipart_data(d, f)
        return self.post("/shuo/statuses/", body=body, headers=headers)
        
    #FIXED
    def get_notes(self, start, count):
        jdata = self.get("/people/%s/notes" % self.alias, 
                {"start-index": start, "max-results": count})
        if jdata and isinstance(jdata, dict):
            contents = jdata.get("entry", [])
            if contents:
                print '------get douban note,len is:', len(contents)
                return [DoubanNoteData(c) for c in contents]
    
    #FIXED
    def get_miniblogs(self, start, count):
        jdata = self.get("/people/%s/miniblog" % self.alias,
                {"start-index": start, "max-results": count})
        if jdata and isinstance(jdata, dict):
            contents = jdata.get("entry",[])
            if contents:
                print '------get douban miniblog,len is:', len(contents)
                return [DoubanMiniBlogData(c) for c in contents]

    def get_albums(self, start, count):
        return self.get("/people/%s/albums" % self.alias, 
                {"start-index": start, "max-results": count})
        
    def get_album(self, album_id):
        return self.get("/album/%s" % album_id)

    def get_album_photos(self, album_id):
        return self.get("/album/%s/photos" % album_id)

    def get_photo(self, photo_id):
        return self.get("/photo/%s" % photo_id)
    
