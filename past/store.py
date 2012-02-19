#-*- coding:utf-8 -*-

import os
import commands

import MySQLdb
import redis

import config 

def init_db():
    cmd = """mysql -h%s -P%s -u%s -p%s < %s""" \
        %(config.DB_HOST, config.DB_PORT, 
            config.DB_USER, config.DB_PASSWD,
            os.path.join(os.path.dirname(__file__), "schema.sql"))
    status, output = commands.getstatusoutput(cmd)

    if status != 0:
        print "init_db fail, output is: %s" %output   

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

db_conn = connect_db()
redis_cache_conn = connect_redis_cache()
redis_conn = connect_redis()
