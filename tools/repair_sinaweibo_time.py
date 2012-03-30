#-*- coding:utf-8 -*-

import sys
sys.path.append('../')

import datetime
import past
from past.store import db_conn, mongo_conn
from past.utils.escape import json_decode

cursor = db_conn.execute("select id from status where category=200")
rows = cursor.fetchall()
cursor and cursor.close()
ids = [x[0] for x in rows]

for x in ids:
    try:
        raw = mongo_conn.get("/status/raw/%s" %x)
        if raw:
            print x
            data = json_decode(raw)
            t = data.get("created_at")
            created_at = datetime.datetime.strptime(t, "%a %b %d %H:%M:%S +0800 %Y")
            db_conn.execute("update status set create_time = %s where id=%s", (created_at, x))
            db_conn.commit()
    except:
        import traceback
        print traceback.format_exc()
        sys.stdout.flush()
