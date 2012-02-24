#-*- coding:utf-8 -*-

from MySQLdb import IntegrityError
from past.corelib.cache import cache, pcache
from past.store import redis_conn, redis_cache_conn, db_conn
from past.utils import randbytes
from past.utils.escape import json_decode, json_encode
from past import config

class User(object):
    def __init__(self, id):
        self.id = str(id)
        self.uid = None
        self.name = None
        self.create_time = None
        self.session_id = None
    
    def __repr__(self):
        return "<User id=%s, name=%s, uid=%s, session_id=%s>" \
                % (self.id, self.name, self.uid, self.session_id)
    __str__ = __repr__

    @classmethod
    def _clear_cache(cls, user_id):
        if user_id:
            redis_cache_conn.delete("user:%s" % user_id)
        redis_cache_conn.delete("user:ids")
        
    @classmethod
    @cache("user:{id}")
    def get(cls, id):
        uid = None
        if isinstance(id, basestring) and not id.isdigit():
            uid = id
        cursor = db_conn.cursor()
        if uid:
            cursor.execute("""select id, uid,name,session_id,time 
                from user where uid=%s""", uid)
        else:
            cursor.execute("""select id, uid,name,session_id,time 
                from user where id=%s""", id)
        row = cursor.fetchone()
        cursor.close()
        if row:
            u = cls(row[0])
            u.uid = str(row[1])
            u.name = row[2]
            u.session_id = row[3]
            u.create_time = row[4]
            return u

        return None

    @classmethod
    def gets(cls, ids):
        return [cls.get(x) for x in ids]

    @classmethod
    @pcache("user:ids")
    def get_ids(cls, start=0, limit=20, order="id desc"):
        cursor = db_conn.cursor()
        sql = """select id from user 
                order by """ + order + """ limit %s, %s"""
        cursor.execute(sql, (start, limit))
        rows = cursor.fetchall()
        cursor.close()
        return [x[0] for x in rows]

    def get_alias(self):
        return UserAlias.gets_by_user_id(self.id)
    
    @classmethod
    def add(cls, name=None, uid=None, session_id=None):
        cursor = db_conn.cursor()
        user = None

        name = "" if name is None else name
        uid = "" if uid is None else uid
        session_id = session_id if session_id else randbytes(8)

        try:
            cursor.execute("""insert into user (uid, name, session_id) 
                values (%s, %s, %s)""", 
                (uid, name, session_id))
            user_id = cursor.lastrowid
            if uid == "":
                cursor.execute("""update user set uid=%s where id=%s""", 
                    (user_id, user_id))
            db_conn.commit()
            cls._clear_cache(None)
            user = cls.get(user_id)
        except IntegrityError:
            db_conn.rollback()
        finally:
            cursor.close()

        return user

    def clear_session(self):
        self.update_session(None)

    def update_session(self, session_id):
        cursor = db_conn.cursor()
        cursor.execute("""update user set session_id=%s where id=%s""", 
                (session_id, self.id))
        cursor.close()
        db_conn.commit()
        User._clear_cache(self.id)

    def set_profile(self, profile):
        redis_conn.set('/profile/%s' %self.id, json_encode(profile))
        return self.get_profile()

    def get_profile(self):
        r = redis_conn.get('/profile/%s' %self.id)
        return json_decode(r) if r else {}
    
    def set_profile_item(self, k, v):
        p = self.get_profile()
        p[k] = v
        self.set_profile(p)
        return self.get_profile()

    def get_profile_item(self, k):
        profile = self.get_profile()
        return profile and profile.get(k)

    ##获取第三方帐号的profile信息
    def get_thirdparty_profile(self, openid_type):
        p = self.get_profile_item(openid_type)
        return json_decode(p) if p else {}
        
    def get_avatar_url(self):
        return self.get_profile().get("avatar_url", "")

    def set_avatar_url(self, url):
        return self.set_profile_item("avatar_url", url)

    def get_icon_url(self):
        return self.get_profile().get("icon_url", "")

    def set_icon_url(self, url):
        return self.set_profile_item("icon_url", url)

class UserAlias(object):

    def __init__(self, id_, type_, alias, user_id):
        self.id = id_
        self.type = type_
        self.alias = alias
        self.user_id = str(user_id)

    def __repr__(self):
        return "<UserAlias type=%s, alias=%s, user_id=%s>" \
                % (self.type, self.alias, self.user_id)
    __str__ = __repr__

    @classmethod
    def get_by_id(cls, id):
        ua = None
        cursor = db_conn.cursor()
        cursor.execute("""select `id`, `type`, alias, user_id from user_alias 
                where id=%s""", id)
        row = cursor.fetchone()
        if row:
            ua = cls(*row)
        cursor.close()

        return ua

    @classmethod
    def get(cls, type_, alias):
        ua = None
        cursor = db_conn.cursor()
        cursor.execute("""select `id`, user_id from user_alias 
                where `type`=%s and alias=%s""", 
                (type_, alias))
        row = cursor.fetchone()
        if row:
            ua = cls(row[0], type_, alias, row[1])
        cursor.close()

        return ua

    @classmethod
    def gets_by_user_id(cls, user_id):
        uas = []
        cursor = db_conn.cursor()
        cursor.execute("""select `id`, `type`, alias from user_alias 
                where user_id=%s""", user_id)
        rows = cursor.fetchall()
        if rows and len(rows) > 0:
            uas = [cls(row[0], row[1], row[2], user_id) for row in rows]
        cursor.close()

        return uas

    @classmethod
    def get_ids(cls, start=0, limit=0):
        ids = []
        cursor = db_conn.cursor()
        if limit == 0:
            limit = 100000000
        cursor.execute("""select `id` from user_alias 
                limit %s, %s""", (start, limit))
        rows = cursor.fetchall()
        if rows and len(rows) > 0:
            ids = [row[0] for row in rows]
        cursor.close()

        return ids

    @classmethod
    def get_by_user_and_type(cls, user_id, type_):
        uas = cls.gets_by_user_id(user_id)
        for x in uas:
            if x.type == type_:
                return x
        return None

    @classmethod
    def bind_to_exists_user(cls, user, type_, alias):
        ua = cls.get(type_, alias)
        if ua:
            return None

        ua = None
        cursor = db_conn.cursor()
        try:
            cursor.execute("""insert into user_alias (`type`,alias,user_id) 
                    values (%s, %s, %s)""", (type_, alias, user.id))
            db_conn.commit()
            ua = cls.get(type_, alias)
        except IntegrityError:
            db_conn.rollback()
        finally:
            cursor.close()

        return ua

    @classmethod
    def create_new_user(cls, type_, alias, name=None):
        if cls.get(type_, alias):
            return None

        user = User.add(name)
        if not user:
            return None

        return cls.bind_to_exists_user(user, type_, alias)

    def get_homepage_url(self):
        if self.type == config.OPENID_TYPE_DICT[config.OPENID_DOUBAN]:
            return u"豆瓣", "%s/people/%s" %(config.DOUBAN_SITE, self.alias)

        if self.type == config.OPENID_TYPE_DICT[config.OPENID_SINA]:
            return u"微博", "%s/%s" %(config.SINA_SITE, self.alias)

        if self.type == config.OPENID_TYPE_DICT[config.OPENID_TWITTER]:
            return u"twitter", "%s/%s" %(config.TWITTER_SITE, self.alias)

        if self.type == config.OPENID_TYPE_DICT[config.OPENID_QQ]:
            ##XXX:腾讯微博比较奇怪
            return u"腾讯微博", "%s/%s" %(config.QQWEIBO_SITE, 
                    User.get(self.user_id).get_thirdparty_profile(self.type).get("uid", ""))

class OAuth2Token(object):
   
    def __init__(self, alias_id, access_token, refresh_token):
        self.alias_id = alias_id
        self.access_token = access_token
        self.refresh_token = refresh_token

    @classmethod
    def get(cls, alias_id):
        ot = None
        cursor = db_conn.cursor()
        cursor.execute("""select access_token, refresh_token  
                from oauth2_token where alias_id=%s order by time desc limit 1""", 
                (alias_id,))
        row = cursor.fetchone()
        if row:
            ot = cls(alias_id, row[0], row[1])

        return ot

    @classmethod
    def add(cls, alias_id, access_token, refresh_token):
        ot = None
        cursor = db_conn.cursor()
        try:
            cursor.execute("""replace into oauth2_token 
                    (alias_id, access_token, refresh_token)
                    values (%s, %s, %s)""", 
                    (alias_id, access_token, refresh_token))
            db_conn.commit()
            ot = cls.get(alias_id)
        except IntegrityError:
            db_conn.rollback()
        finally:
            cursor.close()

        return ot

        
