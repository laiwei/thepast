# -*- coding: utf-8 -*-

import urlparse
import urllib
import config
from past.utils.escape import json_encode, json_decode
from past.utils.logger import logging
from past.utils import httplib2_request
from past.model.status import (DoubanStatusData, DoubanNoteData,
    DoubanMiniBlogData, SinaWeiboStatusData)

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

    def __init__(self, alias, access_token, refresh_token=None,
            api_host = "https://api.weibo.com", api_version=2):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.alias = alias
        self.api_host = api_host
        self.api_version = str(api_version)

        self.apikey = config.APIKEY_DICT.get(config.OPENID_SINA).get("key")
   
    def __repr__(self):
        return '<Douban alias=%s, access_token=%s, refresh_token=%s, \
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
            print '-------sinawebicontent:', contents[-1]
            print '-------len sinawebicontent:', len(contents)
        return [SinaWeiboStatusData(c) for c in contents]

