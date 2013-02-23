#-*- coding:utf-8 -*-

from MySQLdb import IntegrityError
from past.corelib.cache import cache, pcache
from past.store import mc, db_conn

class UserWeixin(object):
    def __init__(self, user_id, weixin_name):
        self.user_id = str(user_id)
        self.weixin_name = weixin_name

    def __repr__(self):
        return "<UserWeixin user_id=%s, weixin_name=%s>" \
                %(self.user_id, self.weixin_name)
    __str__ = __repr__

    @classmethod
    @cache("user_weixin:{weixin_name}")
    def get_by_weixin(cls, weixin_name):
        return cls._find_by("weixin_name", weixin_name)
    
    @classmethod
    def add(cls, user_id, weixin_name):
        cursor = None
        try:
            cursor = db_conn.execute('''insert into user_weixin (user_id, weixin_name)
                    values (%s, %s) on duplicate key update user_id=%s''', (user_id, weixin_name, user_id))
            db_conn.commit()
            cls.clear_cache(user_id, weixin_name)
            return cls.get_by_weixin(weixin_name)
        except IntegrityError:
            db_conn.rollback()
        finally:
            cursor and cursor.close()

    @classmethod
    def clear_cache(cls, user_id, weixin_name):
        mc.delete("user_weixin:%s" % weixin_name)

    @classmethod
    def _find_by(cls, col, value, start=0, limit=1):
        assert limit >= 0
        if limit == 0:
            cursor = db_conn.execute("""select user_id, weixin_name
                    from user_weixin where `""" + col + """`=%s""", value)
        else:
            cursor = db_conn.execute("""select user_id, weixin_name
                    from user_weixin where `""" + col + """`=%s limit %s, %s""", (value, start, limit))
        if limit == 1:
            row = cursor.fetchone()
            cursor and cursor.close()
            return row and cls(*row)
        else:
            rows = cursor.fetchall()
            cursor and cursor.close()
            return [cls(*row) for row in rows]
