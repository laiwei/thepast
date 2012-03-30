#-*- coding:utf-8 -*-

import sys
sys.path.append('../')

from datetime import timedelta
import MySQLdb

import past
from past import config
from past.model.status import Status

def connect_db():
    try:
        conn = MySQLdb.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            passwd=config.DB_PASSWD,
            db="wp_linjuly",
            use_unicode=True,
            charset="utf8")
        return conn
    except Exception, e:
        print "connect db fail:%s" % e
        return None
db_conn = connect_db()

user_id = 34
limit = 250

status_ids = Status.get_ids(user_id, limit=limit, order="create_time desc")

for s in Status.gets(status_ids):
    try:
        _t = ''.join( [x for x in s.text] )

        retweeted_data = s.get_retweeted_data()
        if retweeted_data:
            if isinstance(retweeted_data, basestring):
                _t += retweeted_data
            else:
                _t += retweeted_data.get_content()
        print '---sid:', s.id
        post_author = 1 
        post_date = s.create_time
        post_date_gmt = s.create_time - timedelta(hours=8)
        post_content = _t
        post_title = u"%s" %post_content[:10]
        post_modified = post_date
        post_modified_gmt = post_date_gmt
        post_type = "post"

        post_excerpt = ""
        to_ping = ""
        pinged = ""
        post_content_filtered = ""
        
        cursor = None
        try:
            cursor = db_conn.cursor()
            cursor.execute('''insert into wp_posts (post_author, post_date, post_date_gmt,  post_content,
                    post_excerpt, to_ping, pinged, post_content_filtered,
                    post_title, post_modified, post_modified_gmt, post_type) 
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
                    (post_author, post_date, post_date_gmt, post_content,
                    post_excerpt, to_ping, pinged, post_content_filtered,
                    post_title, post_modified, post_date_gmt, post_type))
            post_id = cursor.lastrowid
            cursor.execute('''update wp_posts set guid = %s''', 
                    "http://www.linjuly.com/?p=%s" %post_id)
            cursor.execute('''insert into wp_term_relationships values(%s,3,0)''', post_id)
            db_conn.commit()
        except Exception, e:
            import traceback; print traceback.format_exc()
            db_conn.rollback()
        finally:
            cursor and cursor.close()
    except Exception, e:
        import traceback; print traceback.format_exc()


#*************************** 1. row ***************************
#                   ID: 8
#          post_author: 1
#            post_date: 2012-01-01 22:29:57
#        post_date_gmt: 2012-01-01 14:29:57
#         post_content: 2011，其实是蛮惨的一年。。。
#           post_title: 我的2011
#         post_excerpt: 
#          post_status: publish
#       comment_status: open
#          ping_status: open
#        post_password: 
#            post_name: %e6%88%91%e7%9a%842011
#              to_ping: 
#               pinged: 
#        post_modified: 2012-03-29 23:31:37
#    post_modified_gmt: 2012-03-29 15:31:37
#post_content_filtered: 
#          post_parent: 0
#                 guid: http://www.linjuly.com/?p=8
#           menu_order: 0
#            post_type: post
#       post_mime_type: 
#        comment_count: 0
#1 row in set (0.00 sec)
#
