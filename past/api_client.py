# -*- coding: utf-8 -*-

import urlparse
import urllib
import tweepy
import config
from past.utils.escape import json_encode, json_decode
from past.utils.logger import logging
from past.utils import httplib2_request
from past.model.data import (DoubanStatusData, DoubanNoteData,
    DoubanMiniBlogData, SinaWeiboStatusData, TwitterStatusData)
from past.model.user import User,UserAlias, OAuth2Token

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
            log.warn("get %s fail, status code=%s, msg=%s" \
                    % (uri, resp.status, content))
        return None

    def post(self):
        raise NotImplementedError

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

    #FIXED
    def get_timeline(self, since_id=None, until_id=None):
        d = {}
        if since_id is not None:
            d["since_id"] = since_id 
        if until_id is not None:
            d["until_id"] = until_id

        contents = self.get("/shuo/statuses/user_timeline/%s" \
                % self.alias, d)
        contents = json_decode(contents) if contents else []
        return [DoubanStatusData(c) for c in contents]

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

    def post(self):
        raise NotImplementedError

    def get_timeline(self, since_id=None, until_id=None, count=200):
        d = {}
        d["uid"] = self.alias
        d["trim_user"] = 0
        if since_id is not None:
            d["since_id"] = since_id 
        if until_id is not None:
            d["max_id"] = until_id

        contents = self.get("/statuses/user_timeline.json", d)
        contents = json_decode(contents).get("statuses", []) if contents else []
        ##debug
        if contents:
            print '-------get sinawebo, len is:', len(contents)
        return [SinaWeiboStatusData(c) for c in contents]

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
    
    def api(self):
        return tweepy.API(self.auth, parser=tweepy.parsers.JSONParser())

    def get_timeline(self, since_id=None, max_id=None, count=200):
        contents = self.api().user_timeline(since_id=since_id, max_id=max_id, count=count)
        if contents:
            print '-------get twitter, len is:', len(contents)
        return [TwitterStatusData(c) for c in contents]

class QQWeibo(object):
    ## alias 指的是用户在第三方网站的uid，比如douban的laiwei
    def __init__(self, alias, access_token, refresh_token=None,
            api_host = "https://graph.qq.com/"):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.alias = alias
        self.api_host = api_host

        self.apikey = config.APIKEY_DICT.get(config.OPENID_QQ).get("key")
   
    def __repr__(self):
        return '<QQWeibo alias=%s, access_token=%s, refresh_token=%s, \
                api_host=%s>' \
                % (self.alias, self.access_token, self.refresh_token, 
                self.api_host)
    __str__ = __repr__



    def get(self, url, extra_dict=None):
        pass

    def post(self):
        raise NotImplementedError

    def get_user_info(self):
        pass

    def get_timeline(self, since_id=None, until_id=None, count=200):
        pass
