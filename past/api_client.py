# -*- coding: utf-8 -*-

import urlparse
import urllib
import tweepy
import config
from past.store import mc
from past.utils.escape import json_encode, json_decode
from past.utils.logger import logging
from past.utils import httplib2_request
from past.model.data import (DoubanNoteData, DoubanStatusData,
    DoubanMiniBlogData, SinaWeiboStatusData, TwitterStatusData,
    QQWeiboStatusData, WordpressData)
from past.model.user import User,UserAlias, OAuth2Token
from past.oauth_login import QQOAuth1Login, DoubanLogin, OAuthLoginError

log = logging.getLogger(__file__)

#TODO: save photo of status

class Douban(object):
    
    def __init__(self, alias, access_token, refresh_token=None, 
            api_host = "https://api.douban.com"):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.api_host = api_host
        self.alias = alias
   
    def __repr__(self):
        return '<Douban alias=%s, access_token=%s, refresh_token=%s, \
                api_host=%s>' % (self.alias, self.access_token, 
                self.refresh_token, self.api_host)
    __str__ = __repr__

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
        if resp.status == 200:
            return content
        else:
            #TODO: 在这里如果access_token过期了需要refresh
            log.warn("get %s fail, status code=%s, msg=%s. go to refresh token" \
                    % (uri, resp.status, content))
            d = config.APIKEY_DICT.get(config.OPENID_DOUBAN)
            login_service = DoubanLogin(d['key'], d['secret'], d['redirect_uri'])
            try:
                login_service.update_tokens(self.refresh_token)
            except OAuthLoginError, e:
                log.warn("refresh token fail: %s" % e)
        return None

    def post(self, url, body, headers=None):
        uri = urlparse.urljoin(self.api_host, url)
        if headers is not None:
            headers.update({"Authorization": "Bearer %s" % self.access_token})
        else:
            headers = {"Authorization": "Bearer %s" % self.access_token}     

        resp, content = httplib2_request(uri, "POST", body=body, headers=headers)
        if resp.status == 200:
            return content
        else:
            log.warn("post %s fail, status code=%s, msg=%s" %(url, resp.status, content))
            return None

    def put(self):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError

    def get_me(self):
        return self.get("/people/%s" % self.alias)

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
        contents = self.get("/shuo/v2/statuses/user_timeline/%s?%s" % (user_id, qs))
        contents = json_decode(contents) if contents else []

        return [DoubanStatusData(c) for c in contents]

    def get_home_timeline(self, since_id=None, until_id=None, count=200):
        qs = {}
        qs['count'] = count
        if since_id is not None:
            qs['since_id'] = since_id
        if until_id is not None:
            qs['until_id'] = until_id
        qs = urllib.urlencode(qs)
        contents = self.get("/shuo/v2/statuses/home_timeline?%s" % qs)
        contents = json_decode(contents) if contents else []

        return [DoubanStatusData(c) for c in contents]

    # 发广播，只限文本
    def post_status(self, text, attach=None):
        qs = {}
        qs["text"] = text
        if attach is not None:
            qs["attachments"] = attach
        qs = urllib.urlencode(qs)
        contents = self.post("/shuo/statuses/", body=qs)

    def post_status_with_image(self, text, image_file):
        from past.utils import encode_multipart_data
        d = {"text": text}
        f = {"image" : image_file}
        body, headers = encode_multipart_data(d, f)
        contents = self.post("/shuo/statuses/", body=body, headers=headers)
        
    #FIXED
    def get_notes(self, start, count):
        contents = self.get("/people/%s/notes" % self.alias, 
                {"start-index": start, "max-results": count})
        contents = json_decode(contents).get("entry",[]) if contents else []
        if contents:
            print '------get douban note,len is:', len(contents)
        return [DoubanNoteData(c) for c in contents]
        
    def get_events(self, start, count):
        return self.get("/people/%s/events" % self.alias, 
                {"start-index": start, "max-results": count})

    def get_events_initiate(self, start, count):
        return self.get("/people/%s/events/initiate" % self.alias, 
                {"start-index": start, "max-results": count})

    def get_events_participate(self, start, count):
        return self.get("/people/%s/events/participate" % self.alias, 
                {"start-index": start, "max-results": count})

    def get_events_wish(self, start, count):
        return self.get("/people/%s/events/wish" % self.alias, 
                {"start-index": start, "max-results": count})
    
    #FIXED
    def get_miniblogs(self, start, count):
        contents = self.get("/people/%s/miniblog" % self.alias,
                {"start-index": start, "max-results": count})
        contents = json_decode(contents).get("entry",[]) if contents else []
        if contents:
            print '------get douban miniblog,len is:', len(contents)
        return [DoubanMiniBlogData(c) for c in contents]

    """
        GET /people/{userID}/collection?cat=book
        GET /people/{userID}/collection?cat=movie
        GET /people/{userID}/collection?cat=music
    """
    def get_collections(self, cat, start, count):
        return self.get("/people/%s/collection" % self.alias, 
                {"cat": cat, "start-index": start, "max-results": count})
        
    def get_collection(self, coll_id):
        return self.get("/collection/%s" % coll_id)

    """cat: book, movie, music"""
    def get_reviews(self, cat, start, count):
        return self.get("/people/%s/reviews" % self.alias, 
                {"cat": cat, "start-index": start, "max-results": count})
       
    def get_review(self, review_id):
        return self.get("/review/%s" % review_id)
   
    def get_recommendations(self, start, count):
        return self.get("/people/%s/recommendations" % self.alias, 
                {"start-index": start, "max-results": count})

    def get_recommendation(self, rec_id):
        return self.get("/recommendation/%s" % rec_id)
    

    def get_albums(self, start, count):
        return self.get("/people/%s/albums" % self.alias, 
                {"start-index": start, "max-results": count})
        
    def get_album(self, album_id):
        return self.get("/album/%s" % album_id)

    def get_album_photos(self, album_id):
        return self.get("/album/%s/photos" % album_id)

    def get_photo(self, photo_id):
        return self.get("/photo/%s" % photo_id)
    
class SinaWeibo(object):
    ## alias 指的是用户在第三方网站的uid，比如douban的laiwei
    def __init__(self, alias, access_token, refresh_token=None,
            api_host = "https://api.weibo.com", api_version=2):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.alias = alias
        self.api_host = api_host
        self.api_version = str(api_version)

        self.apikey = config.APIKEY_DICT.get(config.OPENID_SINA).get("key")
   
    def __repr__(self):
        return '<SinaWeibo alias=%s, access_token=%s, refresh_token=%s, \
                api_host=%s, api_version=%s>' \
                % (self.alias, self.access_token, self.refresh_token, 
                self.api_host, self.api_version)
    __str__ = __repr__

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
        if resp.status == 200:
            return content
        else:
            log.warn("get %s fail, status code=%s, msg=%s" \
                    % (uri, resp.status, content))
        return None

    def post(self, url, body, headers=None):
        uri = urlparse.urljoin(self.api_host, self.api_version)
        uri = urlparse.urljoin(uri, url)

        log.info("posting %s" %url)
        resp, content = httplib2_request(uri, "POST", body=body, headers=headers)
        if resp.status == 200:
            return content
        else:
            log.warn("post %s fail, status code=%s, msg=%s" \
                    %(uri, resp.status, content))
        return None

    def get_timeline(self, since_id=None, until_id=None, count=200):
        d = {}
        d["uid"] = self.alias
        d["trim_user"] = 0
        d["count"] = count
        if since_id is not None:
            d["since_id"] = since_id 
        if until_id is not None:
            d["max_id"] = until_id

        contents = self.get("/statuses/user_timeline.json", d)
        contents = json_decode(contents).get("statuses", []) if contents else []
        ##debug
        if contents:
            print '---get sinawebo succ, result length is:', len(contents)
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

class Twitter(object):
    def __init__(self, alias, apikey=None, apikey_secret=None, access_token=None, access_token_secret=None):
        ua = UserAlias.get(config.OPENID_TYPE_DICT[config.OPENID_TWITTER], alias)
        self.apikey = apikey if apikey is not None else config.APIKEY_DICT[config.OPENID_TWITTER].get("key")
        self.apikey_secret = apikey_secret if apikey_secret is not None else config.APIKEY_DICT[config.OPENID_TWITTER].get("secret")
        
        token = OAuth2Token.get(ua.id)
        self.access_token = access_token if access_token is not None else token.access_token
        self.access_token_secret = access_token_secret if access_token_secret is not None else token.refresh_token

        self.auth = tweepy.OAuthHandler(self.apikey, self.apikey_secret)        
        self.auth.set_access_token(self.access_token, self.access_token_secret)
        
    @classmethod                                                                   
    def get_client(cls, user_id):                                                  
        alias = UserAlias.get_by_user_and_type(user_id,                            
                config.OPENID_TYPE_DICT[config.OPENID_TWITTER])                       
        if not alias:                                                              
            return None                                                            
                                                                                   
        return cls(alias.alias)
    
    def api(self):
        return tweepy.API(self.auth, parser=tweepy.parsers.JSONParser())

    def get_timeline(self, since_id=None, max_id=None, count=200):
        contents = self.api().user_timeline(since_id=since_id, max_id=max_id, count=count)
        return [TwitterStatusData(c) for c in contents]

    def post_status(self, text):
        self.api().update_status(status=text)

class QQWeibo(object):
    ## alias 指的是用户在第三方网站的uid，比如douban的laiwei
    def __init__(self, alias, apikey=None, apikey_secret=None, access_token=None, access_token_secret=None):
        ua = UserAlias.get(config.OPENID_TYPE_DICT[config.OPENID_QQ], alias)
        
        self.apikey = apikey if apikey is not None else config.APIKEY_DICT[config.OPENID_QQ].get("key")
        self.apikey_secret = apikey_secret if apikey_secret is not None else config.APIKEY_DICT[config.OPENID_QQ].get("secret")

        ##TODO:这里的OAuth2Token也变相的存储了OAuth1的token和secret，需要后续改一改
        token = OAuth2Token.get(ua.id)
        self.access_token = access_token if access_token is not None else token.access_token
        self.access_token_secret = access_token_secret if access_token_secret is not None else token.refresh_token

        self.auth = QQOAuth1Login(self.apikey, self.apikey_secret, 
                token=self.access_token, token_secret=self.access_token_secret)

    @classmethod                                                                   
    def get_client(cls, user_id):                                                  
        alias = UserAlias.get_by_user_and_type(user_id,                            
                config.OPENID_TYPE_DICT[config.OPENID_QQ])                       
        if not alias:                                                              
            return None                                                            
                                                                                   
        return cls(alias.alias)
    
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

        contents = self.auth.access_resource("GET", "/statuses/broadcast_timeline", qs)
        if not contents:
            return []

        try:
            contents_ = json_decode(contents)
        except:
            ##XXX:因为腾讯的json数据很2，导致有时候decode的时候会失败，一般都是因为双引号没有转义的问题
            import re
            r = re.sub('=\\"[^ >]*"( |>)', '', contents)
            contents_ = json_decode(r)
        contents = contents_

        if str(contents.get("ret")) != "0":
            return []
        
        data  = contents.get("data")
        info = data and data.get("info")
        print '---status from qqweibo, len is: %s' % len(info)

        return [QQWeiboStatusData(c) for c in info]

    def post_status(self, text):
        #from flask import request
        #qs = {"content": text, "format": "json", "clientip": request.remote_addr,}
        qs = {"content": text, "format": "json", "clientip": "202.38.64.1",}
        return self.auth.access_resource("POST", "/t/add", qs)

    def post_status_with_image(self, text, image_file):
        #from flask import request
        #qs = {"content": text, "format": "json", "clientip": request.remote_addr,}
        qs = {"content": text, "format": "json", "clientip": "202.38.64.1",}
        f = {"pic" : image_file}
        contents = self.auth.access_resource("POST", "/t/add_pic", qs, f)
        
class Wordpress(object):
    
    WORDPRESS_ETAG_KEY = "wordpress:etag:%s"

    ## 同步wordpress rss
    def __init__(self, alias):
        ## alias means wordpress feed uri
        self.alias = alias

    def __repr__(self):
        return "<Wordpress alias=%s>" %(self.alias)
    __str__ = __repr__

    def get_etag(self):
        r = str(Wordpress.WORDPRESS_ETAG_KEY % self.alias)
        return mc.get(r)

    def set_etag(self, etag):
        r = str(Wordpress.WORDPRESS_ETAG_KEY % self.alias)
        mc.set(r, etag)

    def get_feeds(self, refresh=False):
        import feedparser
        etag = self.get_etag()
        if refresh:
            d = feedparser.parse(self.alias)
        else:
            d = feedparser.parse(self.alias, etag=etag)
        if not d:
            return []
        if not (d.status == 200 or d.status == 301):
            log.warning("---get wordpress feeds, status is %s, not valid" % d.status)
            return []

        entries = d.entries
        if not entries:
            return []

        if (not refresh) and hasattr(d,  'etag'):
            self.set_etag(d.etag)
        return [WordpressData(x) for x in entries]

