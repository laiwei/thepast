import sys
sys.path.append('../')

from past.store import db_conn
from past.model.user import User
from past.model.status import Status
from past.model.kv import RawStatus
from past import consts


def remove_user(uid):
    user = User.get(uid)
    if not user:
        print '---no user:%s' % uid

    print "---- delete from user, uid=", uid
    db_conn.execute("delete from user where id=%s", uid)
    db_conn.commit()
    User._clear_cache(uid)

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

    print "---- delete from passwd, uid=", uid
    db_conn.execute("delete from passwd where user_id=%s", uid)
    print "---- delete from sync_task, uid=", uid
    db_conn.execute("delete from sync_task where user_id=%s", uid)
    print "---- delete from user_alias, uid=", uid
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


