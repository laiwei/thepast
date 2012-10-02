#-*- coding:utf-8 -*-

import sys
sys.path.append('../')
import datetime
import os
from MySQLdb import IntegrityError
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
            print "r1"
            #UserProfile.set(row[0], r1)
            Kv.set('/profile/%s' %row[0], r1)
        r2 = mongo_conn.get("/profile/%s" % row[0])
        if r2:
            #Kv.set('/profile/%s' %row[0], r2)
            UserProfile.set(row[0], r2)

def myset(status_id, text, raw):
    cursor = None
    text = json_encode(text) if not isinstance(text, basestring) else text
    raw = json_encode(raw) if not isinstance(raw, basestring) else raw

    db_conn.execute('''replace into raw_status (status_id, text, raw) 
        values(%s,%s,%s)''', (status_id, text, raw))


def move_status():
    STATUS_REDIS_KEY = "/status/text/%s"
    RAW_STATUS_REDIS_KEY = "/status/raw/%s"

    start = 3720000
    limit = 100000
    #r =db_conn.execute("select count(1) from status")
    #total = r.fetchone()[0]
    total = 4423725
    print '----total status:', total
    sys.stdout.flush()

    ef = open("error.log", "a")
    #cf = open("cmd.txt", "w")
    while (start <= int(total)):
        f = open("./midfile.txt", "w")
        print '-------start ', start
        sys.stdout.flush()
        cursor = db_conn.execute("select id from status order by id limit %s,%s", (start, limit))
        rows = cursor.fetchall()
        for row in rows:
            text = mongo_conn.get(STATUS_REDIS_KEY % row[0])
            raw = mongo_conn.get(RAW_STATUS_REDIS_KEY% row[0])
            if text and raw:
                text = json_encode(text) if not isinstance(text, basestring) else text
                raw = json_encode(raw) if not isinstance(raw, basestring) else raw

                db_conn.execute('''replace into raw_status (status_id, text, raw) 
                    values(%s,%s,%s)''', (row[0], text, raw))
        db_conn.commit()
        start += limit


move_user_profile()
move_status()
