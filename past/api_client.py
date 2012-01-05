# -*- coding: utf-8 -*-

import urlparse
import urllib
import config
from past.utils.escape import json_encode, json_decode
from past.utils.logger import logging
from past.utils import httplib2_request
from past.model.status import (DoubanStatusData, DoubanNoteData,
    DoubanMiniBlogData)

log = logging.getLogger(__file__)

class Douban(object):
    
    def __init__(self, alias_id, access_token, refresh_token=None, api_host = "https://api.douban.com"):
        self.alias_id = alias_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.api_host = api_host
   
    def __repr__(self):
        return '<Douban alias_id=%s, access_token=%s, refresh_token=%s,\
                api_host=%s>' % (self.alias_id, 
                self.access_token, self.refresh_token, self.api_host)
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
        return self.get("/people/%s" % self.alias_id)

    def get_me2(self):
        return self.get("/shuo/users/%s" % self.alias_id)

    def get_note(self, note_id):
        return self.get("/note/%s" % note_id)

    #FIXED
    def get_notes(self, start, count):
        contents = self.get("/people/%s/notes" % self.alias_id, 
                {"start-index": start, "max-results": count})
        contents = json_decode(contents).get("entry",[]) if contents else []
        return [DoubanNoteData(c) for c in contents]
        
    def get_events(self, start, count):
        return self.get("/people/%s/events" % self.alias_id, 
                {"start-index": start, "max-results": count})

    def get_events_initiate(self, start, count):
        return self.get("/people/%s/events/initiate" % self.alias_id, 
                {"start-index": start, "max-results": count})

    def get_events_participate(self, start, count):
        return self.get("/people/%s/events/participate" % self.alias_id, 
                {"start-index": start, "max-results": count})

    def get_events_wish(self, start, count):
        return self.get("/people/%s/events/wish" % self.alias_id, 
                {"start-index": start, "max-results": count})
    
    #FIXED
    def get_miniblogs(self, start, count):
        contents = self.get("/people/%s/miniblog" % self.alias_id,
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
                % self.alias_id, d)
        contents = json_decode(contents) if contents else []
        return [DoubanStatusData(c) for c in contents]

    """
        GET /people/{userID}/collection?cat=book
        GET /people/{userID}/collection?cat=movie
        GET /people/{userID}/collection?cat=music
    """
    def get_collections(self, cat, start, count):
        return self.get("/people/%s/collection" % self.alias_id, 
                {"cat": cat, "start-index": start, "max-results": count})
        
    def get_collection(self, coll_id):
        return self.get("/collection/%s" % coll_id)

    """cat: book, movie, music"""
    def get_reviews(self, cat, start, count):
        return self.get("/people/%s/reviews" % self.alias_id, 
                {"cat": cat, "start-index": start, "max-results": count})
       
    def get_review(self, review_id):
        return self.get("/review/%s" % review_id)
   
    def get_recommendations(self, start, count):
        return self.get("/people/%s/recommendations" % self.alias_id, 
                {"start-index": start, "max-results": count})

    def get_recommendation(self, rec_id):
        return self.get("/recommendation/%s" % rec_id)
    

    def get_albums(self, start, count):
        return self.get("/people/%s/albums" % self.alias_id, 
                {"start-index": start, "max-results": count})
        
    def get_album(self, album_id):
        return self.get("/album/%s" % album_id)

    def get_album_photos(self, album_id):
        return self.get("/album/%s/photos" % album_id)

    def get_photo(self, photo_id):
        return self.get("/photo/%s" % photo_id)
    
