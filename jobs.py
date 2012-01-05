#-*- coding:utf-8 -*-

import datetime
import time
from past import config
from past.utils.escape import json_decode, json_encode
from past.store import connect_db, connect_redis
from past.api_client import Douban
from past.model.status import Status, DoubanNoteData, DoubanStatusData, SyncTask
from past.model.user import User, UserAlias, OAuth2Token

db_conn = connect_db()
redis_conn = connect_redis()

while True:
    print '---once again...'
    ids = SyncTask.get_ids()
    task_list = SyncTask.gets(ids)
    if not task_list:
        print '---no task...'
    for t in task_list:
        detail = t.get_detail()

        alias = UserAlias.get_by_user_and_type(t.user_id, 
                config.OPENID_TYPE_DICT[config.OPENID_DOUBAN])
        token = OAuth2Token.get(alias.id)
        client = Douban(alias.alias, token.access_token, token.refresh_token)

        if t.kind == config.SYNC_DOUBAN_NOTE:
            start = detail.get('start', 0)
            count = detail.get('count', 10)
            contents = client.get_notes(start, count)
            contents = json_decode(contents).get("entry", []) if contents else []
            if contents:
                for x in contents:
                    print '----note content:', x
                    d = DoubanNoteData(x)
                    Status.add_from_obj(t.user_id, d, x)
                detail['start'] = detail.get('start', 0) + len(contents)
                detail['uptime'] = datetime.datetime.now()
                t.update_detail(detail)
                
        if t.kind == config.SYNC_DOUBAN_SHUO:
            until_id = detail.get("until_id")
            contents = client.get_timeline(until_id=until_id)
            contents = json_decode(contents) if contents else []
            if contents:
                for x in contents:
                    print '----status content:', x
                    d = DoubanStatusData(x)
                    Status.add_from_obj(t.user_id, d, x)
                detail['until_id'] = DoubanStatusData(contents[-1]).get_origin_id()
                detail['uptime'] = datetime.datetime.now()
                print '----will set detail:',detail, json_encode(detail)
                t.update_detail(detail)

        time.sleep(2)
    
    time.sleep(5)


