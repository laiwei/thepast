#-*- coding:utf-8 -*-

import datetime
import time
from optparse import OptionParser

from past import config
from past.utils.escape import json_encode, json_decode
from past.utils.logger import logging
from past.api_client import Douban, SinaWeibo, Twitter
from past.corelib import category2provider
from past.model.data import (DoubanNoteData, 
        DoubanStatusData, DoubanMiniBlogData)
from past.model.status import Status, SyncTask
from past.model.user import User, UserAlias, OAuth2Token

log = logging.getLogger(__file__)


def _sync(t, old=False):
    alias = None
    provider = category2provider(t.category)
    if provider == config.OPENID_DOUBAN:
        alias = UserAlias.get_by_user_and_type(t.user_id, 
                config.OPENID_TYPE_DICT[config.OPENID_DOUBAN])
    elif provider == config.OPENID_SINA:
        alias = UserAlias.get_by_user_and_type(t.user_id, 
                config.OPENID_TYPE_DICT[config.OPENID_SINA])
    elif provider == config.OPENID_TWITTER:
        pass
        alias = UserAlias.get_by_user_and_type(t.user_id, 
                config.OPENID_TYPE_DICT[config.OPENID_TWITTER])
    if not alias:
        log.warn("no alias...")
        return

    token = OAuth2Token.get(alias.id)
    if not token:
        log.warn("no access token, break...")
        return
    
    client = None
    if provider == config.OPENID_DOUBAN:
        client = Douban(alias.alias, token.access_token, token.refresh_token)
    elif provider == config.OPENID_SINA:
        client = SinaWeibo(alias.alias, token.access_token)
    elif provider == config.OPENID_TWITTER:
        client = Twitter(alias.alias)
    if not client:
        log.warn("get client fail, break...")
        return

    if t.category == config.CATE_DOUBAN_NOTE:
        if old:
            start = Status.get_count_by_cate(t.category, t.user_id)
        else:
            start = 0
        note_list = client.get_notes(start, 50)
        if note_list:
            for x in note_list:
                Status.add_from_obj(t.user_id, x, json_encode(x.get_data()))
    elif t.category == config.CATE_DOUBAN_MINIBLOG:
        if old:
            start = Status.get_count_by_cate(t.category, t.user_id)
        else:
            start = 0
        miniblog_list = client.get_miniblogs(start, 50)
        if miniblog_list:
            for x in miniblog_list:
                Status.add_from_obj(t.user_id, x, json_encode(x.get_data()))
    elif t.category == config.CATE_DOUBAN_STATUS or t.category == config.CATE_SINA_STATUS:
        if old:
            until_id = Status.get_min_origin_id(t.category, t.user_id) #means max_id
            status_list = client.get_timeline(until_id=until_id)
        else:
            since_id = Status.get_min_origin_id(t.category, t.user_id)
            status_list = client.get_timeline(since_id=since_id)
        if status_list:
            for x in status_list:
                Status.add_from_obj(t.user_id, x, json_encode(x.get_data()))
    elif t.category == config.CATE_TWITTER_STATUS:
        if old:
            until_id = Status.get_min_origin_id(t.category, t.user_id) #means max_id
            status_list = client.get_timeline(max_id=until_id)
        else:
            since_id = Status.get_min_origin_id(t.category, t.user_id)
            status_list = client.get_timeline(since_id=since_id)
        if status_list:
            for x in status_list:
                Status.add_from_obj(t.user_id, x, json_encode(x.get_data()))

def sync_helper(cate,old=False):
    log.info("%s syncing old %s... cate=%s" % (datetime.datetime.now(), old, cate))
    ids = SyncTask.get_ids()
    task_list = SyncTask.gets(ids)
    if cate:
        task_list = [x for x in task_list if x.category==cate]
    if not task_list:
        log.warn("no task list, so sleep 10s and continue...")
        return 
    
    log.info("task_list length is %s" % len(task_list))
    for t in task_list:
        _sync(t, old)
        time.sleep(5)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-t", "--time", dest="time", help="sync old or new msg")
    parser.add_option("-c", "--cate", type="int", dest="cate", help="category")
    parser.add_option("-n", "--num", type="int", dest="num", help="run how many times")
    (options, args) = parser.parse_args()
    
    if not options.time or options.time not in ['new', 'old']:
        print 'sync old or new?'
    else:
        old = True if options.time=='old' else False
        cate = options.cate if options.cate else None
        num = options.num if options.num else 1
        for i in xrange(num):
            sync_helper(cate, old)
            time.sleep(5)


##python jobs.py -t old -c 200 -n 2
