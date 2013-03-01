import sys
sys.path.append('../')

from past.store import db_conn
from past.model.user import User
from past.model.status import Status
from past.model.kv import RawStatus
from past import consts
from past import config

from past.utils.logger import logging
log = logging.getLogger(__file__)

suicide_log = logging.getLogger(__file__)
suicide_log.addHandler(logging.FileHandler(config.SUICIDE_LOG))

def remove_user(uid, clear_status=True):
    user = User.get(uid)
    if not user:
        print '---no user:%s' % uid

    suicide_log.info("---- delete from user, uid=%s" %uid)
    db_conn.execute("delete from user where id=%s", uid)
    db_conn.commit()
    User._clear_cache(uid)

    if clear_status:
        cursor = db_conn.execute("select id from status where user_id=%s", uid)
        if cursor:
            rows = cursor.fetchall()
            for row in rows:
                sid = row[0]
                suicide_log.info("---- delete status text, sid=%s" % sid)
                RawStatus.remove(sid)

        suicide_log.info("---- delete from status, uid=" %uid)
        db_conn.execute("delete from status where user_id=%s", uid)
        db_conn.commit()
        Status._clear_cache(uid, None)

    suicide_log.info("---- delete from passwd, uid=%s" %uid)
    db_conn.execute("delete from passwd where user_id=%s", uid)
    suicide_log.info("---- delete from sync_task, uid=%s" % uid)
    db_conn.execute("delete from sync_task where user_id=%s", uid)
    suicide_log.info("---- delete from user_alias, uid=%s" % uid)
    db_conn.execute("delete from user_alias where user_id=%s", uid)
    db_conn.commit()


def remove_status(uid):
    cursor = db_conn.execute("select id from status where user_id=%s", uid)
    if cursor:
        rows = cursor.fetchall()
        for row in rows:
            sid = row[0]
            print "---- delete mongo text, sid=", sid
            RawStatus.remove(sid)

    print "---- delete from status, uid=", uid
    db_conn.execute("delete from status where user_id=%s", uid)
    db_conn.commit()
    Status._clear_cache(uid, None)

if __name__ == "__main__":
    a = sys.argv
    uids = a[1:]
    for uid in uids:
        print "----- remove user:", uid
        remove_user(uid)
        print "----- remove status of user:", uid
        remove_status(uid)


