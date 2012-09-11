#-*- coding:utf-8 -*-

from MySQLdb import IntegrityError

from past.corelib.cache import cache
from past.store import db_conn
from past.utils.escape import json_encode, json_decode

class Kv(object):
    def __init__(self, key, val, time):
        self.key = key
        self.val = val
        self.time = time

    @classmethod
    def get(cls, key):
        cursor = db_conn.execute('''select key, value, time from kv 
                where key=%s''', key)
        row = cursor.fetchone()
        if row:
            return cls(*row)
        cursor and cursor.close()

    @classmethod
    def set(cls, key, val):
        cursor = None
        val = json_encode(val) if not isinstance(val, basestring) else val

        try:
            cursor = db_conn.execute('''replace into kv(key, val) 
                values(%s,%s)''', (key, val))
            db_conn.commit()
        except IntegrityError:
            db_conn.rollback()

        cursor and cursor.close()

    @classmethod
    def remove(cls, key):
        cursor = None
        try:
            cursor = db_conn.execute('''delete from kv where key = %s''', key)
            db_conn.commit()
        except IntegrityError:
            db_conn.rollback()
        cursor and cursor.close()

class UserProfile(object):
    def __init__(self, user_id, val, time):
        self.user_id = user_id
        self.val = val
        self.time = time

    @classmethod
    def get(cls, user_id):
        cursor = db_conn.execute('''select user_id, value, time from user_profile
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
            cursor = db_conn.execute('''replace into user_profile (user_id, val) 
                values(%s,%s)''', (user_id, val))
            db_conn.commit()
        except IntegrityError:
            db_conn.rollback()

        cursor and cursor.close()

    @classmethod
    def remove(cls, user_id):
        cursor = None
        try:
            cursor = db_conn.execute('''delete from user_profile where user_id= %s''', user_id)
            db_conn.commit()
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
        except IntegrityError:
            db_conn.rollback()

        cursor and cursor.close()

    @classmethod
    def remove(cls, status_id):
        cursor = None
        try:
            cursor = db_conn.execute('''delete from raw_status where status_id = %s''', status_id )
            db_conn.commit()
        except IntegrityError:
            db_conn.rollback()
        cursor and cursor.close()
