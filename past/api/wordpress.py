# -*- coding: utf-8 -*-

from past.store import mc
from past.model.data import WordpressData
from past.utils.logger import logging

log = logging.getLogger(__file__)

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

    def get_feeds(self, refresh=True):
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
