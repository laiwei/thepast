#-*- coding:utf-8 -*-

import datetime
import time
from optparse import OptionParser

from past import config
from past.utils.escape import json_encode, json_decode
from past.utils.logger import logging
from past.utils import datetime2timestamp

from past.api.douban import Douban
from past.api.sina import SinaWeibo
from past.api.qqweibo import QQWeibo
from past.api.renren import Renren
from past.api.instagram import Instagram
from past.api.twitter import TwitterOAuth1
from past.api.wordpress import Wordpress

from past.corelib import category2provider
from past.model.status import Status, SyncTask
from past.model.user import User, UserAlias, OAuth2Token

log = logging.getLogger(__file__)

def sync(t, old=False):
    if not t:
        print 'no such task'
        return 0
    log.info("the sync task is :%s" % t)
    try:
        alias = None
        provider = category2provider(t.category)

        alias = UserAlias.get_by_user_and_type(t.user_id,
                config.OPENID_TYPE_DICT[provider])
        if not alias:
            log.warn("no alias...")
            return 0

        token = OAuth2Token.get(alias.id)
        if not token:
            log.warn("no access token, break...")
            return 0
        
        client = None
        if provider == config.OPENID_DOUBAN:
            client = Douban.get_client(alias.user_id)
        elif provider == config.OPENID_SINA:
            client = SinaWeibo.get_client(alias.user_id)
        elif provider == config.OPENID_TWITTER:
            client = TwitterOAuth1.get_client(alias.user_id)
        elif provider == config.OPENID_QQ:
            client = QQWeibo.get_client(alias.user_id)
        elif provider == config.OPENID_RENREN:
            client = Renren.get_client(alias.user_id)
        elif provider == config.OPENID_INSTAGRAM:
            client = Instagram.get_client(alias.user_id)
        if not client:
            log.warn("get client fail, break...")
            return 0

        if t.category == config.CATE_DOUBAN_NOTE:
            if old:
                start = Status.get_count_by_cate(t.category, t.user_id)
            else:
                start = 0
            note_list = client.get_notes(start, 50)
            if note_list:
                for x in note_list:
                    Status.add_from_obj(t.user_id, x, json_encode(x.get_data()))
                return len(note_list)
        elif t.category == config.CATE_DOUBAN_MINIBLOG:
            if old:
                start = Status.get_count_by_cate(t.category, t.user_id)
            else:
                start = 0
            miniblog_list = client.get_miniblogs(start, 50)
            if miniblog_list:
                for x in miniblog_list:
                    Status.add_from_obj(t.user_id, x, json_encode(x.get_data()))
                return len(miniblog_list)
        elif t.category == config.CATE_DOUBAN_STATUS:
            origin_min_id = Status.get_min_origin_id(t.category, t.user_id)
            if old:
                log.info("will get douban status order than %s..." % origin_min_id)
                status_list = client.get_timeline(until_id=origin_min_id)
            else:
                log.info("will get douban status newer than %s..." % origin_min_id)
                status_list = client.get_timeline(since_id=origin_min_id, count=20)
            if status_list:
                log.info("get douban status succ, len is %s" % len(status_list))
                for x in status_list:
                    Status.add_from_obj(t.user_id, x, json_encode(x.get_data()))
                
        elif t.category == config.CATE_SINA_STATUS:
            origin_min_id = Status.get_min_origin_id(t.category, t.user_id) #means the earliest id
            origin_max_id = Status.get_max_origin_id(t.category, t.user_id) #meas the latest id
            if old:
                log.info("will get sinaweibo order than %s..." % origin_min_id)
                status_list = client.get_timeline(until_id=origin_min_id)
                ## 如果根据max_id拿不到数据，那么根据page再fetch一次或者until_id - 1
                if status_list and len(status_list) < 20 and origin_min_id is not None:
                    log.info("again will get sinaweibo order than %s..." % (int(origin_min_id)-1))
                    status_list = client.get_timeline(until_id=int(origin_min_id)-1)
            else:
                log.info("will get sinaweibo newer than %s..." % origin_max_id)
                status_list = client.get_timeline(since_id=origin_max_id, count=50)
            if status_list:
                log.info("get sinaweibo succ, len is %s" % len(status_list))
                for x in status_list:
                    Status.add_from_obj(t.user_id, x, json_encode(x.get_data()))
                return len(status_list)
        elif t.category == config.CATE_TWITTER_STATUS:
            origin_min_id = Status.get_min_origin_id(t.category, t.user_id)
            origin_max_id = Status.get_max_origin_id(t.category, t.user_id)
            if old:
                log.info("will get tweets order than %s..." % origin_min_id)
                status_list = client.get_timeline(max_id=origin_min_id)
            else:
                log.info("will get tweets newer than %s..." % origin_max_id)
                status_list = client.get_timeline(since_id=origin_max_id, count=50)
            if status_list:
                log.info("get tweets succ, len is %s" % len(status_list))
                for x in status_list:
                    Status.add_from_obj(t.user_id, x, json_encode(x.get_data()))
                return len(status_list)
        elif t.category == config.CATE_QQWEIBO_STATUS:
            if old:
                oldest_create_time = Status.get_oldest_create_time(t.category, t.user_id)
                log.info("will get qqweibo order than %s" % oldest_create_time)
                if oldest_create_time is not None:
                    oldest_create_time = datetime2timestamp(oldest_create_time)
                status_list = client.get_old_timeline(oldest_create_time, reqnum=200)
            else:
                log.info("will get qqweibo new timeline")
                status_list = client.get_new_timeline(reqnum=20)
            if status_list:
                log.info("get qqweibo succ, result length is:%s" % len(status_list))
                for x in status_list:
                    Status.add_from_obj(t.user_id, x, json_encode(x.get_data()))
                return len(status_list)
        elif t.category == config.CATE_RENREN_STATUS:
            if old:
                count = 100
                total_count = Status.get_count_by_cate(t.category, t.user_id)
                page = int(total_count / count) + 1
                log.info("will get older renren status, page=%s, count=%s" %(page, count))
                status_list = client.get_timeline(page, count)
            else:
                count = 20
                page = 1
                log.info("will get newest renren status, page=%s, count=%s" %(page, count))
                status_list = client.get_timeline(page, count)
            if status_list:
                log.info("get renren status succ, result length is:%s" % len(status_list))
                for x in status_list:
                    Status.add_from_obj(t.user_id, x, json_encode(x.get_data()))
                return len(status_list)
        elif t.category == config.CATE_RENREN_BLOG:
            if old:
                count = 50
                total_count = Status.get_count_by_cate(t.category, t.user_id)
                page = int(total_count / count) + 1
                log.info("will get older renren blog, page=%s, count=%s" %(page, count))
                blogs = client.get_blogs(page, count)
            else:
                count = 20
                page = 1
                log.info("will get newest renren blog, page=%s, count=%s" %(page, count))
                blogs = client.get_blogs(page, count)
            if blogs:
                uid = blogs.get("uid")
                blog_ids = filter(None, [v.get("id") for v in blogs.get("blogs", [])])
                log.info("get renren blog ids succ, result length is:%s" % len(blog_ids))
                for blog_id in blog_ids:
                    blog = client.get_blog(blog_id, uid)
                    if blog:
                        Status.add_from_obj(t.user_id, blog, json_encode(blog.get_data()))
                return len(blog_ids)
        elif t.category == config.CATE_RENREN_ALBUM:
            status_list = client.get_albums()
            if status_list:
                log.info("get renren album succ, result length is:%s" % len(status_list))
                for x in status_list:
                    Status.add_from_obj(t.user_id, x, json_encode(x.get_data()))
                return len(status_list)
        elif t.category == config.CATE_RENREN_PHOTO:
            albums_ids = Status.get_ids(user_id=t.user_id, limit=1000, cate=config.CATE_RENREN_ALBUM)
            albums = Status.gets(albums_ids)
            if not albums:
                return 0
            for x in albums:
                d = x.get_data()
                if not d:
                    continue
                aid = d.get_origin_id()
                size = int(d.get_size())
                count = 50
                for i in xrange(1, size/count + 2):
                    status_list = client.get_photos(aid, i, count)
                    if status_list:
                        log.info("get renren photo of album %s succ, result length is:%s" \
                                % (aid, len(status_list)))
                        for x in status_list:
                            Status.add_from_obj(t.user_id, x, json_encode(x.get_data()))

        elif t.category == config.CATE_INSTAGRAM_STATUS:
            origin_min_id = Status.get_min_origin_id(t.category, t.user_id) #means the earliest id
            origin_max_id = Status.get_max_origin_id(t.category, t.user_id) #means the latest id
            if old:
                log.info("will get instagram earlier than %s..." % origin_min_id)
                status_list = client.get_timeline(max_id=origin_min_id)
            else:
                log.info("will get instagram later than %s..." % origin_max_id)
                status_list = client.get_timeline(min_id=origin_max_id, count=50)
            if status_list:
                log.info("get instagram succ, len is %s" % len(status_list))
                for x in status_list:
                    Status.add_from_obj(t.user_id, x, json_encode(x.get_data()))
                return len(status_list)
    except Exception, e:
        print "---sync_exception_catched:", e
    return 0

def sync_wordpress(t, refresh=True):
    if not t:
        log.warning('no_wordpress_sync_task')
        return

    #一个人可以有多个wordpress的rss源地址
    rs = UserAlias.gets_by_user_id(t.user_id)
    uas = []
    for x in rs:
        if x.type == config.OPENID_TYPE_DICT[config.OPENID_WORDPRESS]:
            uas.append(x)
    if not uas:
        log.warning('no_wordpress_alias')
        return
    for ua in uas:
        try:
            client = Wordpress(ua.alias)
            rs = client.get_feeds(refresh)
            if rs:
                log.info("get wordpress succ, result length is:%s" % len(rs))
                for x in rs:
                    Status.add_from_obj(t.user_id, x, json_encode(x.get_data()))
                return 
        except Exception, e:
            print "---sync_exception_catched:", e

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
        try:
            if t.category == config.CATE_WORDPRESS_POST:
                sync_wordpress(t)
            else:
                sync(t, old)
        except Exception, e:
            import traceback
            print "%s %s" % (datetime.datetime.now(), traceback.format_exc())

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-t", "--time", dest="time", help="sync old or new msg")
    parser.add_option("-c", "--cate", type="int", dest="cate", help="category")
    parser.add_option("-n", "--num", type="int", dest="num", help="run how many times")
    (options, args) = parser.parse_args()
    
    if not options.time:
        options.time = 'new'
    if options.time not in ['new', 'old']:
        options.time = 'new'
    
    old = True if options.time=='old' else False
    cate = options.cate if options.cate else None
    num = options.num if options.num else 1
    for i in xrange(num):
        sync_helper(cate, old)


##python jobs.py -t old -c 200 -n 2
