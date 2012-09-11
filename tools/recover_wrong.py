#-*- coding:utf-8 -*-

import sys
sys.path.append('../')

from datetime import timedelta

from past.store import  db_conn
from past.model.kv import RawStatus

with open("ids.txt") as f:
    for id_ in f:
        id_ = id_.rstrip("\n")

        print id_
        cursor = db_conn.execute("delete from status where id=%s", id_)
        db_conn.commit()

        RawStatus.remove(id_)

        #cursor = db_conn.execute("select * from status where id=%s", id_)
        #print cursor.fetchone()
