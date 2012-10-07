#-*- coding:utf-8 -*-

import os
import commands
import datetime

import MySQLdb
import redis
import memcache

from past.utils.escape import json_decode, json_encode
from past import config 

def init_db():
    cmd = """mysql -h%s -P%s -u%s -p%s < %s""" \
        % (config.DB_HOST, config.DB_PORT, 
            config.DB_USER, config.DB_PASSWD,
            os.path.join(os.path.dirname(__file__), "schema.sql"))
    status, output = commands.getstatusoutput(cmd)

    if status != 0:
        print "init_db fail, output is: %s" % output   

    return status
        
def connect_db():
    try:
        conn = MySQLdb.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            passwd=config.DB_PASSWD,
            db=config.DB_NAME,
            use_unicode=True,
            charset="utf8")
        return conn
    except Exception, e:
        print "connect db fail:%s" % e
        return None

def connect_redis():
    return redis.Redis(config.REDIS_HOST, config.REDIS_PORT)

def connect_redis_cache():
    return redis.Redis(config.REDIS_CACHE_HOST, config.REDIS_CACHE_PORT)

def connect_mongo(dbname="thepast"):
    import pymongo
    conn = pymongo.connection.Connection('localhost')
    db = conn.thepast
    db = getattr(conn, dbname)
    return db and getattr(db, dbname)

class MongoDB(object):
    def __init__(self, dbname="thepast"):
        self.dbname = dbname
        self._conn = connect_mongo(self.dbname)

    def connect(self):
        self._conn = connect_mongo(self.dbname)
        return self._conn

    def get(self, k):
        d = {"k":k}
        r = self._conn.find_one(d)
        if r:
            return r.get("v")
        return None

    def mget(self, keys):
        d = {"k": {"$in" : keys}}
        rs = self._conn.find(d)
        return [r["v"] for r in rs]

    def set(self, k, v):
        self._conn.update({"k":k},{"k":k, "v":v}, upsert=True)

    def remove(self, k):
        self._conn.remove({"k":k})

    def get_connection(self):
        return self._conn or self.connect()

class DB(object):
    
    def __init__(self):
        self._conn = connect_db()

    def connect(self):
        self._conn = connect_db()
        return self._conn

    def execute(self, *a, **kw):
        cursor = kw.pop('cursor', None)
        try:
            cursor = cursor or self._conn.cursor()
            cursor.execute(*a, **kw)
        except (AttributeError, MySQLdb.OperationalError):
            print 'debug, %s re-connect to mysql' % datetime.datetime.now()
            self._conn and self._conn.close()
            self.connect()
            cursor = self._conn.cursor()
            cursor.execute(*a, **kw)
        return cursor
        
    def commit(self):
        return self._conn and self._conn.commit()

    def rollback(self):
        return self._conn and self._conn.rollback()

def connect_memcached():
    mc = memcache.Client(['%s:%s' % (config.MEMCACHED_HOST, config.MEMCACHED_PORT)], debug=0)
    return mc

db_conn = DB()
mc = redis_cache_conn = connect_memcached()
#redis_conn = connect_redis()
#mongo_conn = MongoDB()
