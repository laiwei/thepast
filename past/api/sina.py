# -*- coding: utf-8 -*-

import urllib
import urlparse
from past import config
from past.utils.logger import logging
from past.utils.escape import json_decode
from past.utils import httplib2_request

from past.model.user import User, UserAlias, OAuth2Token
from past.model.data import SinaWeiboUser 
from past.model.data import SinaWeiboStatusData

from .oauth2 import OAuth2
from .error import OAuthLoginError, OAuthTokenExpiredError

log = logging.getLogger(__file__)

class SinaWeibo(OAuth2):

    authorize_uri = 'https://api.weibo.com/oauth2/authorize'
    access_token_uri = 'https://api.weibo.com/oauth2/access_token' 
    api_host = "https://api.weibo.com"

    def __init__(self, alias=None, access_token=None, refresh_token=None, 
            api_version="2"):

        self.api_version = api_version
        d = config.APIKEY_DICT[config.OPENID_SINA]
        super(SinaWeibo, self).__init__(provider = config.OPENID_SINA, 
                apikey = d["key"], 
                apikey_secret = d["secret"], 
                redirect_uri = d["redirect_uri"],
                alias=alias, 
                access_token=access_token, 
                refresh_token=refresh_token)

    @classmethod
    def get_client(cls, user_id):
        alias = UserAlias.get_by_user_and_type(user_id, 
                config.OPENID_TYPE_DICT[config.OPENID_SINA])
        if not alias:
            return None

        token = OAuth2Token.get(alias.id)
        if not token:
            return None

        return cls(alias.alias, token.access_token, token.refresh_token)

    def check_result(self, uri, resp, content):
        #{"error":"expired_token","error_code":21327,"request":"/2/statuses/update.json"}
        #log.debug("---sina check result, status: %s, resp: %s, content: %s" %(resp.status, resp, content))
        jdata = json_decode(content) if content else None
        if jdata and isinstance(jdata, dict):
            error_code = jdata.get("error_code")
            error = jdata.get("error")
            request_api = jdata.get("request")
            user_id = self.user_alias and self.user_alias.user_id or None
            excp = OAuthTokenExpiredError(user_id,
                    config.OPENID_TYPE_DICT[config.OPENID_SINA], 
                    "%s:%s:%s" %(error_code, error, request_api))
            if error_code and isinstance(error_code, int):
                error_code = int(error_code)
                if error_code >= 21301 and error_code <= 21399:
                    excp.set_the_profile()
                    raise excp
                else:
                    log.warning("get %s fail, error_code=%s, error_msg=%s" \
                        % (uri, error_code, error))
            else:
                excp.clear_the_profile()
                return jdata

    def get(self, url, extra_dict=None):
        uri = urlparse.urljoin(self.api_host, self.api_version)
        uri = urlparse.urljoin(uri, url)
        if extra_dict is None:
            extra_dict = {}
        if not "access_token" in extra_dict:
            extra_dict["access_token"] = self.access_token
        if not "source" in extra_dict:
            extra_dict["source"] = self.apikey

        if extra_dict:
            qs = urllib.urlencode(extra_dict)
            if "?" in uri:
                uri = "%s&%s" % (uri, qs)
            else:
                uri = "%s?%s" % (uri, qs)
        log.info('getting %s...' % uri)

        resp, content = httplib2_request(uri, "GET")
        content_json = self.check_result(uri, resp, content)
        return content_json

    def post(self, url, body, headers=None):
        uri = urlparse.urljoin(self.api_host, self.api_version)
        uri = urlparse.urljoin(uri, url)

        log.info("posting %s" %url)
        resp, content = httplib2_request(uri, "POST", body=body, headers=headers)
        content_json = self.check_result(uri, resp, content)
        log.info("post to sina return:%s" % content_json)
        return content_json

    def get_user_info(self, uid=None):
        d = {}
        d["uid"] = uid or ""
        jdata = self.get("/users/show.json", d)
        if jdata and isinstance(jdata, dict):
            return SinaWeiboUser(jdata)

    def get_timeline(self, since_id=None, until_id=None, count=100):
        d = {}
        d["uid"] = self.alias
        d["trim_user"] = 0
        d["count"] = count
        if since_id is not None:
            d["since_id"] = since_id 
        if until_id is not None:
            d["max_id"] = until_id

        r = self.get("/statuses/user_timeline.json", d)
        contents = r and r.get("statuses", [])
        if contents and isinstance(contents, list):
            print '---get sinawebo succ, result length is:', len(contents)
            return [SinaWeiboStatusData(c) for c in contents]

    ## 新浪微博也很2，通过page可以拿到过往的所有微博
    def get_timeline_by_page(self, page=1, count=100):
        d = {}
        d["uid"] = self.alias
        d["trim_user"] = 0
        d["count"] = count
        d["page"] = page

        r = self.get("/statuses/user_timeline.json", d)
        contents = r and r.get("statuses", [])
        if contents and isinstance(contents, list):
            print '---get sinawebo page %s succ, result length is: %s' %(page, len(contents))
            return [SinaWeiboStatusData(c) for c in contents]

    def post_status(self, text):
        qs = {}
        qs["status"] = text
        qs["access_token"] = self.access_token
        body = urllib.urlencode(qs)
        contents = self.post("/statuses/update.json", body=body)

    def post_status_with_image(self, text, image_file):
        from past.utils import encode_multipart_data
        d = {"status": text, "access_token": self.access_token}
        f = {"pic" : image_file}
        body, headers = encode_multipart_data(d, f)
        contents = self.post("/statuses/upload.json", body=body, headers=headers)

