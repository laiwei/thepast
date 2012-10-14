#-*- coding:utf-8 -*-

import sys
sys.path.append("../")

activate_this = '../env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import time
from past.store import db_conn
from send_reminding import send_reconnect

if __name__ == "__main__":
    cursor = db_conn.execute("select max(id) from user")
    row = cursor.fetchone()
    cursor and cursor.close()
    max_uid = row and row[0]
    max_uid = int(max_uid)
    t = 0
    for uid in xrange(4,max_uid + 1):
    #for uid in xrange(4, 5):
        if t >= 100:
            t = 0
            time.sleep(5)
        send_reconnect(uid)
        time.sleep(1)
        t += 1
        sys.stdout.flush()

