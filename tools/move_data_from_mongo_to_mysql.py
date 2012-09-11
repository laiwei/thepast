#-*- coding:utf-8 -*-

import sys
sys.path.append('../')
import datetime

from past.store import mongo_conn, db_conn
from past.model.kv import UserProfile, RawStatus, Kv
from past.utils.escape import json_decode, json_encode

def move_user_profile():
    RAW_USER_REDIS_KEY = "/user/raw/%s" 

    cursor = db_conn.execute("select id from user order by id")
    rows = cursor.fetchall()
    cursor and cursor.close()
    for row in rows:
        print '--------user raw id:', row[0]
        sys.stdout.flush()
        r1 = mongo_conn.get(RAW_USER_REDIS_KEY % row[0])
        if r1:
            UserProfile.set(row[0], r1)
        r2 = mongo_conn.get("/profile/%s" % row[0])
        if r2:
            Kv.set('/profile/%s' %row[0], r2)

def move_status():
    STATUS_REDIS_KEY = "/status/text/%s"
    RAW_STATUS_REDIS_KEY = "/status/raw/%s"

    start = 0
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
        for row in rows:
            keys = [STATUS_REDIS_KEY % row[0], RAW_STATUS_REDIS_KEY % row[0]]
            values = mongo_conn.mget(keys)
            for row in values:
                RawStatus.set(row[0], values[0], values[1])
        start += limit


move_user_profile()
#move_status()
