#-*- coding:utf-8 -*-

import sys
sys.path.append("../")

activate_this = '../env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import datetime
import time
from collections import defaultdict

from past.utils.sendmail import send_mail
from past.store import db_conn

if __name__ == "__main__":

    t = datetime.datetime.now() - datetime.timedelta(days=90)
    cursor = db_conn.execute("""select alias_id from oauth2_token where time < %s""", t)
    rows = cursor.fetchall()
    cursor and cursor.close()

    user_and_alias = defaultdict(list)

    for row in rows:
        alias_id = row[0]
        c = db_conn.execute("""select `type`, user_id, alias from user_alias where id=%s""", alias_id)
        r = cursor.fetchone()
        c and c.close()

        if r:
            user_and_alias[r[1]].append([r[0], r[2]])
    with open("expire.user", "w") as f:
        for k,v in user_and_alias.items():
            f.write("%s : %s" %(k,v))

