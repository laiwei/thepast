#-*- coding:utf-8 -*-

import sys
sys.path.append('../')

from past.store import mongo_conn, redis_conn, db_conn
from past.utils.escape import json_decode, json_encode

def move_user_profile():
    RAW_USER_REDIS_KEY = "/user/raw/%s" 

    cursor = db_conn.execute("select id from user")
    rows = cursor.fetchall()
    cursor and cursor.close()
    for row in rows:
        print '--------user raw id:', row[0]
        r = redis_conn.get(RAW_USER_REDIS_KEY % row[0])
        if r:
            mongo_conn.set(RAW_USER_REDIS_KEY % row[0], r)
        r2 = redis_conn.get("/profile/%s" % row[0])
        print "from redis", type(r2), r2
        if r2:
            mongo_conn.set("/profile/%s" % row[0], r2)

def move_status():
    STATUS_REDIS_KEY = "/status/text/%s"
    RAW_STATUS_REDIS_KEY = "/status/raw/%s"

    start = 0
    limit = 10000
    r =db_conn.execute("select count(1) from status")
    total = r.fetchone()[0]
    print '----total status:', total

    while (start <= int(total)):
        print '-------start ', start
        cursor = db_conn.execute("select id from status order by id limit %s,%s", (start, limit))
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                id_ = row[0]
                r = redis_conn.get(STATUS_REDIS_KEY % id_)
                if r:
                    mongo_conn.set(STATUS_REDIS_KEY % id_, r)

                r = redis_conn.get(RAW_STATUS_REDIS_KEY % id_)
                if r:
                    mongo_conn.set(RAW_STATUS_REDIS_KEY % id_, r)
        start += limit

move_user_profile()
move_status()
