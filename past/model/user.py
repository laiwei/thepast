#-*- coding:utf-8 -*-

import re
from MySQLdb import IntegrityError
from past.corelib.cache import cache, pcache
from past.store import mc, db_conn
from past.utils import randbytes
from past.utils.escape import json_decode, json_encode
from .kv import Kv, UserProfile
from past import config

class User(object):
    UID_RE = r'^[a-z][0-9a-zA-Z_.-]{3,15}'
    UID_MAX_LEN = 16
    UID_MIN_LEN = 4

    def __init__(self, id):
        self.id = str(id)
        self.uid = None
        self.name = None
        self.create_time = None
        self.session_id = None
    
    def __repr__(self):
        return "<User id=%s, uid=%s, session_id=%s>" \
                % (self.id, self.uid, self.session_id)
    __str__ = __repr__

    @classmethod
    def _clear_cache(cls, user_id):
        if user_id:
            mc.delete("user:%s" % user_id)
            UserProfile.clear_cache(user_id)
        mc.delete("user:ids")
        
    @classmethod
    @cache("user:{id}")
    def get(cls, id):
        uid = None
        if isinstance(id, basestring) and not id.isdigit():
            uid = id
        cursor = None
        if uid:
            cursor = db_conn.execute("""select id, uid,name,session_id,time 
                from user where uid=%s""", uid)
        else:
            cursor = db_conn.execute("""select id, uid,name,session_id,time 
                from user where id=%s""", id)
        row = cursor.fetchone()
        cursor and cursor.close()
        if row:
            u = cls(row[0])
            u.uid = str(row[1])
            u.name = row[2]
            u.session_id = row[3]
            u.create_time = row[4]
            return u

        return None

    @classmethod
    @cache("email2user:{email}")
    def get_user_by_email(cls, email):
        cursor = db_conn.execute('''select user_id from passwd 
                where email=%s''', email)
        row = cursor.fetchone()
        cursor and cursor.close()
        return row and cls.get(row[0])

    @classmethod
    @cache("alias2user:{type_}{alias}")
    def get_user_by_alias(cls, type_, alias):
        cursor = db_conn.execute('''select user_id from user_alias
            where type=%s and alias=%s''', (type_, alias))
        row = cursor.fetchone()
        cursor and cursor.close()
        return row and cls.get(row[0])

    @classmethod
    def gets(cls, ids):
        return [cls.get(x) for x in ids]

    @classmethod
    @pcache("user:ids")
    def get_ids(cls, start=0, limit=20):
        sql = """select id from user 
                order by id desc limit %s, %s"""
        cursor = db_conn.execute(sql, (start, limit))
        rows = cursor.fetchall()
        cursor and cursor.close()
        return [x[0] for x in rows]

    @classmethod
    @pcache("user:ids:asc")
    def get_ids_asc(cls, start=0, limit=20):
        sql = """select id from user 
                order by id asc limit %s, %s"""
        cursor = db_conn.execute(sql, (start, limit))
        rows = cursor.fetchall()
        cursor and cursor.close()
        return [x[0] for x in rows]

    def get_alias(self):
        return UserAlias.gets_by_user_id(self.id)
    
    @cache("user_email:{self.id}")
    def get_email(self):
        cursor = db_conn.execute('''select email from passwd 
                where user_id=%s''', self.id)
        row = cursor.fetchone()
        cursor and cursor.close()
        return row and row[0]

    def set_email(self, email):
        cursor = None
        try:
            cursor = db_conn.execute('''replace into passwd (user_id, email) values (%s,%s)''',
                    (self.id, email))
            db_conn.commit()
            return True
        except IntegrityError:
            db_conn.rollback()
            return False
        finally:
            mc.delete("user_email:%s" % self.id)
            cursor and cursor.close()
            
    @classmethod
    def add(cls, name=None, uid=None, session_id=None):
        cursor = None
        user = None

        name = "" if name is None else name
        uid = "" if uid is None else uid
        session_id = session_id if session_id else randbytes(8)

        try:
            cursor = db_conn.execute("""insert into user (uid, name, session_id) 
                values (%s, %s, %s)""", 
                (uid, name, session_id))
            user_id = cursor.lastrowid
            if uid == "":
                cursor = db_conn.execute("""update user set uid=%s where id=%s""", 
                    (user_id, user_id), cursor=cursor)
            db_conn.commit()
            cls._clear_cache(None)
            user = cls.get(user_id)
        except IntegrityError:
            db_conn.rollback()
        finally:
            cursor and cursor.close()

        return user

    def clear_session(self):
        self.update_session(None)

    def update_session(self, session_id):
        cursor = db_conn.execute("""update user set session_id=%s where id=%s""", 
                (session_id, self.id))
        cursor and cursor.close()
        db_conn.commit()
        User._clear_cache(self.id)

    def update_uid(self, uid):
        assert isinstance(uid, basestring)
        if self.id != self.uid:
            return False, "already_set"

        if uid == self.uid:
            return True, "same_with_old"

        if len(uid) > User.UID_MAX_LEN:
            return False, u"太长了，不能超过%s" %User.UID_MAX_LEN
        if len(uid) < User.UID_MIN_LEN:
            return False, u"太短了，不能小于%s" %User.UID_MIN_LEN
        uid_re = re.compile(User.UID_RE)
        if not uid_re.match(uid):
            return False, u"只能包括字母数字和.-_"
        
        uid = uid.lower()
        if uid in ["user", "pdf", "explore", "home", "visual", "settings", "admin", "past", "connect", "bind",
            "i", "notes", "note", "status", "share", "timeline", "post", "login", "logout", "sync", "about", 
            "connect", "dev", "api", "thepast", "thepast.me", ]:
            return False, u"被系统占用了:)"
            
        try:
            cursor = db_conn.execute("""update user set uid=%s where id=%s""", 
                    (uid, self.id))
            db_conn.commit()
            User._clear_cache(self.id)
            return True, u"设置成功"
        except IntegrityError:
            db_conn.rollback()
            return False, u"被别人占用了:)"
        finally:
            cursor and cursor.close()

        return False, "fail"
            

    def set_profile(self, profile):
        UserProfile.set(self.id, json_encode(profile))
        return self.get_profile()

    def get_profile(self):
        r = UserProfile.get(self.id)
        p = r.val if r else ""
        try:
            return json_decode(p) if p else {}
        except ValueError, e:
            print '------decode profile fail:', e
            return {}
    
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
        if isinstance(p, dict):
            return p
        else:
            r = json_decode(p) if p else {}
            return r

    def set_thirdparty_profile_item(self, openid_type, k, v):
        p = self.get_thirdparty_profile(openid_type)
        p[k] = v
        self.set_profile_item(openid_type, p)
        
    def get_avatar_url(self):
        return self.get_profile().get("avatar_url", "")

    def set_avatar_url(self, url):
        return self.set_profile_item("avatar_url", url)

    def get_icon_url(self):
        return self.get_profile().get("icon_url", "")

    def set_icon_url(self, url):
        return self.set_profile_item("icon_url", url)

    def is_pdf_ready(self):
        from past.utils.pdf import is_user_pdf_file_exists
        return is_user_pdf_file_exists(self.id)

    def get_dev_tokens(self):
        from past.model.user_tokens import UserTokens
        ids = UserTokens.get_ids_by_user_id(self.id)
        return [UserTokens.get(x) for x in ids] or []

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
        cursor = db_conn.execute("""select `id`, `type`, alias, user_id from user_alias 
                where id=%s""", id)
        row = cursor.fetchone()
        if row:
            ua = cls(*row)
        cursor and cursor.close()

        return ua

    @classmethod
    def get(cls, type_, alias):
        ua = None
        cursor = db_conn.execute("""select `id`, user_id from user_alias 
                where `type`=%s and alias=%s""", 
                (type_, alias))
        row = cursor.fetchone()
        if row:
            ua = cls(row[0], type_, alias, row[1])
        cursor and cursor.close()

        return ua

    @classmethod
    def gets_by_user_id(cls, user_id):
        uas = []
        cursor = db_conn.execute("""select `id`, `type`, alias from user_alias 
                where user_id=%s""", user_id)
        rows = cursor.fetchall()
        if rows and len(rows) > 0:
            uas = [cls(row[0], row[1], row[2], user_id) for row in rows]
        cursor and cursor.close()

        return uas

    @classmethod
    def get_ids(cls, start=0, limit=0):
        ids = []
        if limit == 0:
            limit = 100000000
        cursor = db_conn.execute("""select `id` from user_alias 
                limit %s, %s""", (start, limit))
        rows = cursor.fetchall()
        if rows and len(rows) > 0:
            ids = [row[0] for row in rows]
        cursor and cursor.close()

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
        cursor = None
        try:
            cursor = db_conn.execute("""insert into user_alias (`type`,alias,user_id) 
                    values (%s, %s, %s)""", (type_, alias, user.id))
            db_conn.commit()
            ua = cls.get(type_, alias)
        except IntegrityError:
            db_conn.rollback()
        finally:
            cursor and cursor.close()

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
            return config.OPENID_TYPE_NAME_DICT[self.type], \
                    "%s/people/%s" %(config.DOUBAN_SITE, self.alias), \
                    config.OPENID_DOUBAN

        if self.type == config.OPENID_TYPE_DICT[config.OPENID_SINA]:
            return config.OPENID_TYPE_NAME_DICT[self.type], \
                    "%s/%s" %(config.SINA_SITE, self.alias), \
                    config.OPENID_SINA

        ##FIXME:twitter的显示的不对
        if self.type == config.OPENID_TYPE_DICT[config.OPENID_TWITTER]:
            u = User.get(self.user_id)
            return config.OPENID_TYPE_NAME_DICT[self.type],\
                    "%s/#!%s" %(config.TWITTER_SITE, u.name),\
                    config.OPENID_TWITTER

        if self.type == config.OPENID_TYPE_DICT[config.OPENID_QQ]:
            ##XXX:腾讯微博比较奇怪
            return config.OPENID_TYPE_NAME_DICT[self.type],\
                    "%s/%s" %(config.QQWEIBO_SITE, \
                    User.get(self.user_id).get_thirdparty_profile(self.type).get("uid", "")), \
                    config.OPENID_QQ

        if self.type == config.OPENID_TYPE_DICT[config.OPENID_WORDPRESS]:
            ##FIXME: wordpress显示rss地址代替blog地址
            return config.OPENID_TYPE_NAME_DICT[self.type],\
                    self.alias, config.OPENID_WORDPRESS
        if self.type == config.OPENID_TYPE_DICT[config.OPENID_RENREN]:
            return config.OPENID_TYPE_NAME_DICT[self.type],\
                    "%s/%s" %(config.RENREN_SITE, self.alias), config.OPENID_RENREN
        if self.type == config.OPENID_TYPE_DICT[config.OPENID_INSTAGRAM]:
            user = User.get_user_by_alias(self.type, self.alias)
            profile = user and user.get_thirdparty_profile(self.type)
            uid = profile and profile.get("uid", "")
            return config.OPENID_TYPE_NAME_DICT[self.type],\
                    config.INSTAGRAM_USER_PAGE %uid, config.OPENID_INSTAGRAM


class OAuth2Token(object):
   
    def __init__(self, alias_id, access_token, refresh_token):
        self.alias_id = alias_id
        self.access_token = access_token
        self.refresh_token = refresh_token

    @classmethod
    def get(cls, alias_id):
        ot = None
        cursor = db_conn.execute("""select access_token, refresh_token  
                from oauth2_token where alias_id=%s order by time desc limit 1""", 
                (alias_id,))
        row = cursor.fetchone()
        if row:
            ot = cls(alias_id, row[0], row[1])
        cursor and cursor.close()
        return ot

    @classmethod
    def add(cls, alias_id, access_token, refresh_token):
        ot = None
        cursor = None
        try:
            cursor = db_conn.execute("""replace into oauth2_token 
                    (alias_id, access_token, refresh_token)
                    values (%s, %s, %s)""", 
                    (alias_id, access_token, refresh_token))
            db_conn.commit()
            ot = cls.get(alias_id)
        except IntegrityError:
            db_conn.rollback()
        finally:
            cursor and cursor.close()

        return ot


class Confirmation(object):
    def __init__(self, random_id, text, time):
        self.random_id = random_id
        self.text = text
        self.time = time
    
    @classmethod
    def get_by_random_id(cls, random_id):
        cursor = db_conn.execute('''select text, time from confirmation 
                where random_id=%s''', random_id)
        row = cursor.fetchone()
        cursor and cursor.close()
        if row:
            return cls(random_id, row[0], row[1])
    
    def delete(self):
        Confirmation.delete_by_random_id(self.random_id)

    @classmethod
    def delete_by_random_id(cls, random_id):
        db_conn.execute('''delete from confirmation 
                where random_id=%s''', random_id)
        db_conn.commit()

    @classmethod
    def add(cls, random_id, text):
        cursor = None
        try:
            cursor = db_conn.execute('''insert into confirmation (random_id, text) values(%s, %s)''',
                    (random_id, text))
            db_conn.commit()
            return True
        except IntegrityError:
            db_conn.rollback()
        finally:
            cursor and cursor.close()


class PdfSettings(object):
    def __init__(self, user_id, time):
        self.user_id = user_id
        self.time = time

    @classmethod
    def _clear_cache(cls, user_id=None):
        if user_id:
            mc.delete("pdf_settings:u%s" % user_id)
        mc.delete("pdf_settings:all_uids")
            

    @classmethod
    @cache("pdf_settings:all_uids")
    def get_all_user_ids(cls):
        cursor = db_conn.execute('''select user_id from pdf_settings''')
        rows = cursor.fetchall()
        cursor and cursor.close()
        return [str(row[0]) for row in rows]

    @classmethod
    @cache("pdf_settings:u{user_id}")
    def is_user_id_exists(cls, user_id):
        cursor = db_conn.execute('''select user_id from pdf_settings where user_id=%s''', user_id)
        row = cursor.fetchone()
        cursor and cursor.close()
        return True if row else False

    @classmethod
    def add_user_id(cls, user_id):
        cursor = None
        try:
            cursor = db_conn.execute('''insert into pdf_settings (user_id) values (%s)''', user_id)
            db_conn.commit()
            cls._clear_cache(user_id)
            return True
        except IntegrityError:
            db_conn.rollback()
        finally:
            cursor and cursor.close()

    @classmethod
    def remove_user_id(cls, user_id):
        cursor = db_conn.execute('''delete from pdf_settings where user_id=%s''', user_id)
        db_conn.commit()
        cls._clear_cache(user_id)

