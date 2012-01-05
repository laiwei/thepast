#-*- coding:utf-8 -*-

import datetime
import time
from past import config
from past.utils.escape import json_encode, json_decode
from past.utils.logger import logging
from past.store import connect_db, connect_redis
from past.api_client import Douban
from past.model.status import (Status, DoubanNoteData, 
        DoubanStatusData, DoubanMiniBlogData, SyncTask
from past.model.user import User, UserAlias, OAuth2Token

db_conn = connect_db()
redis_conn = connect_redis()
log = logging.getLogger(__file__)

while True:
    log.info("%s syncing..." % datetime.datetime.now())
    ids = SyncTask.get_ids()
    task_list = SyncTask.gets(ids)
    if not task_list:
        log.warn("no task list, so sleep 10s and continue...")
        time.sleep(10)
        break
    
    log.info("task_list length is %s" % len(task_list))
    for t in task_list:
        detail = t.get_detail()
        log.info("task detail is %s" % detail)

        alias = UserAlias.get_by_user_and_type(t.user_id, 
                config.OPENID_TYPE_DICT[config.OPENID_DOUBAN])
        if not alias:
            log.warn("no alias, break...")
            break

        token = OAuth2Token.get(alias.id)
        if not token:
            log.warn("no access token, break...")
            break

        client = Douban(alias.alias, token.access_token, token.refresh_token)
        if not client:
            log.warn("get client fail, break...")
            break

        if t.category == config.CATE_DOUBAN_NOTE:
            start = detail.get('start', 0)
            count = detail.get('count', 10)
            contents = client.get_notes(start, count)
            contents = json_decode(contents).get("entry", []) if contents else []
            if contents:
                for x in contents:
                    d = DoubanNoteData(x)
                    Status.add_from_obj(t.user_id, d, json_encode(x))
                detail['start'] = detail.get('start', 0) + len(contents)
                detail['uptime'] = datetime.datetime.now()
                t.update_detail(detail)
        elif t.category == config.CATE_DOUBAN_MINIBLOG:
            start = detail.get('start', 0)
            count = detail.get('count', 10)
            contents = client.get_miniblogs(start, count)
            contents = json_decode(contents).get("entry", []) if contents else []
            if contents:
                for x in contents:
                    d = DoubanMiniBlogData(x)
                    Status.add_from_obj(t.user_id, d, json_encode(x))
                detail['start'] = detail.get('start', 0) + len(contents)
                detail['uptime'] = datetime.datetime.now()
                t.update_detail(detail)

        elif t.category == config.CATE_DOUBAN_STATUS:
            until_id = detail.get("until_id")
            contents = client.get_timeline(until_id=until_id)
            contents = json_decode(contents) if contents else []
            if contents:
                for x in contents:
                    d = DoubanStatusData(x)
                    Status.add_from_obj(t.user_id, d, json_encode(x))
                detail['until_id'] = DoubanStatusData(contents[-1]).get_origin_id()
                detail['uptime'] = datetime.datetime.now()
                t.update_detail(detail)

        time.sleep(5)
    
    time.sleep(5)


