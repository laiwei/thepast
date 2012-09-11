#-*- coding:utf-8 -*-

import sys
sys.path.append('../')
import datetime

from past.store import mongo_conn, db_conn
from past.utils.escape import json_decode, json_encode

def move_user_profile():
    RAW_USER_REDIS_KEY = "/user/raw/%s" 

    cursor = db_conn.execute("select id from user order by id")
    rows = cursor.fetchall()
    cursor and cursor.close()
    for row in rows:
        print '--------user raw id:', row[0]
        sys.stdout.flush()
        r = redis_conn.get(RAW_USER_REDIS_KEY % row[0])
        if r:
            mongo_conn.set(RAW_USER_REDIS_KEY % row[0], r)
        r2 = redis_conn.get("/profile/%s" % row[0])
        if r2:
            mongo_conn.set("/profile/%s" % row[0], r2)

def move_status():
    STATUS_REDIS_KEY = "/status/text/%s"
    RAW_STATUS_REDIS_KEY = "/status/raw/%s"

    start = 318003
    limit = 2500
    r =db_conn.execute("select count(1) from status")
    total = r.fetchone()[0]
    print '----total status:', total
    sys.stdout.flush()

    while (start <= int(total)):
        print '-------start ', start
        sys.stdout.flush()
        cursor = db_conn.execute("select id from status order by id limit %s,%s", (start, limit))
        rows = cursor.fetchall()
        if rows:
            keys = [STATUS_REDIS_KEY % row[0] for row in rows]
            values = redis_conn.mget(*keys)
            print '+++ mget text:', datetime.datetime.now()
            docs = []
            for i in xrange(0, len(keys)):
                if values[i]:
                    docs.append({"k":keys[i], "v":values[i]})
            mongo_conn.get_connection().insert(docs)
            ##mongo_conn.set(keys[i], values[i])
            print '+++ inserted text:', datetime.datetime.now()

            keys = [RAW_STATUS_REDIS_KEY % row[0] for row in rows]
            values = redis_conn.mget(*keys)
            print '+++ mget raw:', datetime.datetime.now()
            docs = []
            for i in xrange(0, len(keys)):
                if values[i]:
                    docs.append({"k":keys[i], "v":values[i]})
            mongo_conn.get_connection().insert(docs)
            print '+++ inserted raw:', datetime.datetime.now()

        start += limit

#move_user_profile()
move_status()
