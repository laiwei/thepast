# -*- coding: utf-8 -*-

import urllib
import urlparse
from past import config
from past.utils.logger import logging
from past.utils.escape import json_decode
from past.utils import httplib2_request

from past.model.user import User, UserAlias, OAuth2Token
from past.model.data import InstagramUser
from past.model.data import InstagramStatusData 

from .oauth2 import OAuth2
from .error import OAuthLoginError, OAuthTokenExpiredError

log = logging.getLogger(__file__)

class Instagram(OAuth2):

    authorize_uri = 'https://api.instagram.com/oauth/authorize/'
    access_token_uri = 'https://api.instagram.com/oauth/access_token' 
    api_host = 'https://api.instagram.com'

    def __init__(self, alias=None, access_token=None, refresh_token=None, api_version="v1"):
        self.api_version = api_version
        d = config.APIKEY_DICT[config.OPENID_INSTAGRAM]
        super(Instagram, self).__init__(provider = config.OPENID_INSTAGRAM, 
                apikey = d["key"], 
                apikey_secret = d["secret"], 
                redirect_uri = d["redirect_uri"],
                scope = "basic likes comments relationships",
                alias=alias, 
                access_token=access_token, 
                refresh_token=refresh_token)

    @classmethod
    def get_client(cls, user_id):
        alias = UserAlias.get_by_user_and_type(user_id, 
                config.OPENID_TYPE_DICT[config.OPENID_INSTAGRAM])
        if not alias:
            return None

        token = OAuth2Token.get(alias.id)
        if not token:
            return None

        return cls(alias.alias, token.access_token, token.refresh_token)

    def _request(self, api, method="GET", extra_dict=None):
        uri = urlparse.urljoin(self.api_host, api)
        if extra_dict is None:
            extra_dict = {}

        params = {
            "access_token": self.access_token,
        }
        params.update(extra_dict)
        qs = urllib.urlencode(params)
        uri = "%s?%s" % (uri, qs)

        log.info('getting %s...' % uri)
        resp, content = httplib2_request(uri, method)
        if resp.status == 200:
            return json_decode(content) if content else None
        else:
            log.warn("get %s fail, status code=%s, msg=%s" \
                    % (uri, resp.status, content))

    def get_user_info(self, uid=None):
        uid = uid or self.user_alias.alias or "self"
        jdata = self._request("/v1/users/%s" % uid, "GET")
        if jdata and isinstance(jdata, dict):
            return InstagramUser(jdata.get("data"))

    def get_timeline(self, uid=None, min_id=None, max_id=None, count=100):
        d = {}
        d["count"] = count
        if min_id:
            d["min_id"] = min_id
        if max_id:
            d["max_id"] = max_id
        uid = uid or self.alias or "self"

        contents = self._request("/v1/users/%s/media/recent" %uid, "GET", d)
        ##debug
        if contents and isinstance(contents, dict):
            code = str(contents.get("meta", {}).get("code", ""))
            if code == "200":
                data = contents.get("data", [])
                print '---get instagram feed succ, result length is:', len(data)
                return [InstagramStatusData(c) for c in data]

    def get_home_timeline(self, uid=None, min_id=None, max_id=None, count=100):
        d = {}
        d["count"] = count
        if min_id:
            d["min_id"] = min_id
        if max_id:
            d["max_id"] = max_id
        uid = uid or self.alias or "self"

        contents = self._request("/v1/users/%s/feed" %uid, "GET", d)
        ##debug
        if contents and isinstance(contents, dict):
            code = str(contents.get("meta", {}).get("code", ""))
            if code == "200":
                data = contents.get("data", [])
                print '---get instagram home_timeline succ, result length is:', len(data)
                return [InstagramStatusData(c) for c in data]
