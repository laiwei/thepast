#-*- coding:utf-8 -*-

from MySQLdb import IntegrityError

from past.corelib.cache import cache
from past.store import db_conn, mc
from past.utils.escape import json_encode, json_decode

class Kv(object):
    def __init__(self, key_, val, time):
        self.key_ = key_
        self.val = val
        self.time = time

    @classmethod
    def clear_cache(cls, key_):
        mc.delete("mc_kv:%s" %key_)

    @classmethod
    @cache("mc_kv:{key_}")
    def get(cls, key_):
        cursor = db_conn.execute('''select `key`, value, time from kv 
                where `key`=%s''', key_)
        row = cursor.fetchone()
        if row:
            return cls(*row)
        cursor and cursor.close()

    @classmethod
    def set(cls, key_, val):
        cursor = None
        val = json_encode(val) if not isinstance(val, basestring) else val

        try:
            cursor = db_conn.execute('''replace into kv(`key`, value) 
                values(%s,%s)''', (key_, val))
            db_conn.commit()
            cls.clear_cache(key_)
        except IntegrityError:
            db_conn.rollback()

        cursor and cursor.close()

    @classmethod
    def remove(cls, key_):
        cursor = None
        try:
            cursor = db_conn.execute('''delete from kv where `key` = %s''', key_)
            db_conn.commit()
            cls.clear_cache(key_)
        except IntegrityError:
            db_conn.rollback()
        cursor and cursor.close()

class UserProfile(object):
    def __init__(self, user_id, val, time):
        self.user_id = user_id
        self.val = val
        self.time = time

    @classmethod
    def clear_cache(cls, user_id):
        mc.delete("mc_user_profile:%s" %user_id)

    @classmethod
    @cache("mc_user_profile:{user_id}")
    def get(cls, user_id):
        cursor = db_conn.execute('''select user_id, profile, time from user_profile
                where user_id=%s''', user_id)
        row = cursor.fetchone()
        if row:
            return cls(*row)
        cursor and cursor.close()

    @classmethod
    def set(cls, user_id, val):
        cursor = None
        val = json_encode(val) if not isinstance(val, basestring) else val

        try:
            cursor = db_conn.execute('''replace into user_profile (user_id, profile) 
                values(%s,%s)''', (user_id, val))
            db_conn.commit()
            cls.clear_cache(user_id)
        except IntegrityError:
            db_conn.rollback()

        cursor and cursor.close()

    @classmethod
    def remove(cls, user_id):
        cursor = None
        try:
            cursor = db_conn.execute('''delete from user_profile where user_id= %s''', user_id)
            db_conn.commit()
            cls.clear_cache(user_id)
        except IntegrityError:
            db_conn.rollback()
        cursor and cursor.close()

class RawStatus(object):
    def __init__(self, status_id, text, raw, time):
        self.status_id = status_id
        self.text = text
        self.raw = raw
        self.time = time

    @classmethod
    def clear_cache(cls, status_id):
        mc.delete("mc_raw_status:%s" %status_id)

    @classmethod
    @cache("mc_raw_status:{status_id}")
    def get(cls, status_id):
        cursor = db_conn.execute('''select status_id, text, raw, time from raw_status 
                where status_id=%s''', status_id)
        row = cursor.fetchone()
        if row:
            return cls(*row)
        cursor and cursor.close()

    @classmethod
    def set(cls, status_id, text, raw):
        cursor = None
        text = json_encode(text) if not isinstance(text, basestring) else text
        raw = json_encode(raw) if not isinstance(raw, basestring) else raw

        try:
            cursor = db_conn.execute('''replace into raw_status (status_id, text, raw) 
                values(%s,%s,%s)''', (status_id, text, raw))
            db_conn.commit()
            cls.clear_cache(status_id)
        except IntegrityError:
            db_conn.rollback()

        cursor and cursor.close()

    @classmethod
    def remove(cls, status_id):
        cursor = None
        try:
            cursor = db_conn.execute('''delete from raw_status where status_id = %s''', status_id )
            db_conn.commit()
            cls.clear_cache(status_id)
        except IntegrityError:
            db_conn.rollback()
        cursor and cursor.close()
