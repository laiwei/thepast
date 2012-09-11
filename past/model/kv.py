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
        pass

    @classmethod
    def set(cls, key, val):
        pass

    @classmethod
    def remove(cls, key):
        pass

class UserProfile(object):
    def __init__(self, user_id, val, time):
        self.user_id = user_id
        self.val = val
        self.time = time

    @classmethod
    def get(cls, user_id):
        pass

    @classmethod
    def set(cls, user_id, val):
        pass

    @classmethod
    def remove(cls, user_id):
        pass

class RawStatus(object):
    def __init__(self, status_id, text, raw, time):
        self.status_id = status_id
        self.text = text
        self.raw = raw
        self.time = time

    @classmethod
    def get(cls, status_id):
        pass

    @classmethod
    def set(cls, status_id, text, raw):
        cursor = None
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
