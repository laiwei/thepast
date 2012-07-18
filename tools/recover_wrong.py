#-*- coding:utf-8 -*-

import sys
sys.path.append('../')

from datetime import timedelta

from past.store import  mongo_conn, db_conn

with open("ids.txt") as f:
    for id_ in f:
        id_ = id_.rstrip("\n")

        print id_
        cursor = db_conn.execute("delete from status where id=%s", id_)
        db_conn.commit()

        mongo_conn.remove("/status/text/%s" %id_)
        mongo_conn.remove("/status/raw/%s" %id_)

        #cursor = db_conn.execute("select * from status where id=%s", id_)
        #print cursor.fetchone()
