import sys
sys.path.append('../')

from past.store import db_conn
from past.model.user import User
from past import consts

def update_p2t():
    cursor = db_conn.execute("select id from user")
    rows = cursor and cursor.fetchall()
    cursor and cursor.close()
    for row in rows:
        uid = row[0]
        user = User.get(uid)
        if not user:
            print '---no user %s' %uid
            return

        old_p = user.get_profile_item("user_privacy")
        if not old_p or old_p == consts.USER_PRIVACY_PUBLIC:
            user.set_profile_item("user_privacy", consts.USER_PRIVACY_THEPAST)
        print '---updated user %s' %uid

update_p2t()
