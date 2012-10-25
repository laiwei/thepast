#-*- coding:utf-8 -*-
# for dev -> api

from MySQLdb import IntegrityError
from past.corelib.cache import cache, pcache
from past.store import mc, db_conn

class UserTokens(object):
    def __init__(self, id, user_id, token, device):
        self.id = id
        self.user_id = str(user_id)
        self.token = str(token)
        self.device = device

    def __repr__(self):
        return "<UserTokens id=%s, user_id=%s, token=%s, device=%s>" \
                % (self.id, self.user_id, self.token, self.device)
    __str__ = __repr__

    @classmethod
    @cache("user_token:{id}")
    def get(cls, id):
        return cls._find_by("id", id)

    @classmethod
    @cache("user_token:{token}")
    def get_by_token(cls, token):
        return cls._find_by("token", token)

    @classmethod
    @cache("user_token_ids:{user_id}")
    def get_ids_by_user_id(cls, user_id):
        r = cls._find_by("user_id", user_id, limit=0)
        if r:
            return [r.id for x in r]
        else:
            return []
    
    @classmethod
    def add(cls, user_id, token, device=""):
        cursor = None
        try:
            cursor = db_conn.execute('''insert into user_tokens (user_id, token, device)
                    values (%s, %s, %s)''', (user_id, token, device))
            id_ = cursor.lastrowid
            db_conn.commit()
            return cls.get(id_)
        except IntegrityError:
            db_conn.rollback()
        finally:
            cursor and cursor.close()

    def remove(self):
        db_conn.execute('''delete from user_tokens where id=%s''', self.id)
        db_conn.commit()
        self._clear_cache()

    def _clear_cache(self):
        mc.delete("user_token:%s" % self.id)
        mc.delete("user_token:%s" % self.token)
        mc.delete("user_token_ids:%s" % self.user_id)

    @classmethod
    def _find_by(cls, col, value, start=0, limit=1):
        assert limit >= 0
        if limit == 0:
            cursor = db_conn.execute("""select id, user_id, token, device 
                    from user_tokens where `""" + col + """`=%s""", value)
        else:
            cursor = db_conn.execute("""select id, user_id, token, device 
                    from user_tokens where `""" + col + """`=%s limit %s, %s""", (value, start, limit))
        if limit == 1:
            row = cursor.fetchone()
            cursor and cursor.close()
            return row and cls(*row)
        else:
            rows = cursor.fetchall()
            cursor and cursor.close()
            return [cls(*row) for row in rows]
