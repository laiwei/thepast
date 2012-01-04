#-*- coding:utf-8 -*-

import datetime
import time
from json import loads as json_decode
from json import dumps as json_encode
from past import config
from past.store import connect_db, connect_redis
from past.api_client import Douban
from past.model.status import Status, DoubanNoteData, SyncTask
from past.model.user import User, UserAlias, OAuth2Token

db_conn = connect_db()
redis_conn = connect_redis()

while True:
    print '--start'
    cursor = db_conn.cursor()
    cursor.execute("""select id, kind, user_id, time from sync_task""")
    while True:
        r = cursor.fetchone()
        print '----------r:',r
        if not r:
            break
        user_id = r[2]
        kind = r[1]
        detail = redis_conn.get(SyncTask.kv_db_key_task %r[0])
        detail = json_decode(detail) if detail is not None else {}
        
        start = detail.get('start', 0)
        count = detail.get('count', 10)

        alias = UserAlias.get_by_user_and_type(user_id, 
                config.OPENID_TYPE_DICT[config.OPENID_DOUBAN])
        token = OAuth2Token.get(alias.id)
        client = Douban(alias.alias, token.access_token, token.refresh_token)

        if kind == config.SYNC_DOUBAN_NOTE:
            content = client.get_notes(start, count)
            content = json_decode(content) if content else []
            for x in content:
                d = DoubanNoteData(x)
                Status.add_from_obj(d)
            start += len(content)
            redis_conn.set("", start)
                
        if kind == config.SYNC_DOUBAN_SHUO:
            content = client.get_timeline(start)

        print content
        time.sleep(2)
    
    time.sleep(5)


