#-*- coding:utf-8 -*-

from MySQLdb import IntegrityError

from past import config
from past.utils.escape import json_encode, json_decode
from past.utils.logger import logging
from past.store import connect_redis, connect_db
from .user import UserAlias
from .data import DoubanMiniBlogData, DoubanNoteData, SinaWeiboStatusData

log = logging.getLogger(__file__)

redis_conn = connect_redis()
db_conn = connect_db()

class Status(object):
    
    STATUS_REDIS_KEY = "/status/text/%s"
    RAW_STATUS_REDIS_KEY = "/status/raw/%s"

    def __init__(self, id, user_id, origin_id, 
            create_time, site, category, title=""):
        self.id = str(id)
        self.user_id = str(user_id)
        self.origin_id = str(origin_id)
        self.create_time = create_time
        self.site = site
        self.category = category
        self.title = title
        self.text = json_decode(redis_conn.get(
                self.__class__.STATUS_REDIS_KEY % self.id))
        self.raw = json_decode(redis_conn.get(
                self.__class__.RAW_STATUS_REDIS_KEY % self.id))
        self.origin_user_id = UserAlias.get_by_user_and_type(self.user_id, self.site).alias

    def __repr__(self):
        return "<Status id=%s, user_id=%s, origin_id=%s, cate=%s, title=%s>" \
            %(self.id, self.user_id, self.origin_id, self.category, self.title)
    __str__ = __repr__

    @classmethod
    def add(cls, user_id, origin_id, create_time, site, category, title, 
            text=None, raw=None):
        status = None
        cursor = db_conn.cursor()
        try:
            cursor.execute("""insert into status 
                    (user_id, origin_id, create_time, site, category, title)
                    values (%s,%s,%s,%s,%s,%s)""",
                    (user_id, origin_id, create_time, site, category, title))
            db_conn.commit()
            status_id = cursor.lastrowid
            if text is not None:
                redis_conn.set(cls.STATUS_REDIS_KEY %status_id, json_encode(text))
            if raw is not None:
                redis_conn.set(cls.RAW_STATUS_REDIS_KEY %status_id, raw)
            status = cls.get(status_id)
        except IntegrityError:
            log.warning("add status duplicated, ignore...")
            db_conn.rollback()
        finally:
            cursor.close()

        return status

    @classmethod
    def add_from_obj(cls, user_id, d, raw=None):
        origin_id = d.get_origin_id()
        create_time = d.get_create_time()
        title = d.get_title()
        content = d.get_content()

        site = d.site
        category = d.category
        user_id = user_id

        cls.add(user_id, origin_id, create_time, site, category, 
                title, content, raw)

    @classmethod
    def get(cls, status_id):
        status = None
        cursor = db_conn.cursor()
        cursor.execute("""select user_id, origin_id, create_time, site, 
                category, title from status 
                where id=%s""", status_id)
        row = cursor.fetchone()
        if row:
            status = cls(status_id, *row)
        cursor.close()

        return status

    @classmethod
    def get_ids(cls, user_id, start=0, limit=20, order="create_time", cate=None):
        cursor = db_conn.cursor()
        if not user_id:
            return []
        if cate is not None:
            sql = """select id from status where user_id=%s and category=%s
                    order by """ + order + """ desc limit %s,%s""" 
            cursor.execute(sql, (user_id, cate, start, limit))
        else:
            sql = """select id from status where user_id=%s
                    order by """ + order + """ desc limit %s,%s""" 
            cursor.execute(sql, (user_id, start, limit))
        rows = cursor.fetchall()
        cursor.close()
        return [x[0] for x in rows]
    
    @classmethod
    def gets(cls, ids):
        return [cls.get(x) for x in ids]

    @classmethod
    def get_max_origin_id(cls, cate, user_id):
        cursor = db_conn.cursor()
        cursor.execute('''select max(origin_id) from status 
            where category=%s and user_id=%s''', (cate, user_id))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return 0

    @classmethod
    def get_min_origin_id(cls, cate, user_id):
        cursor = db_conn.cursor()
        cursor.execute('''select min(origin_id) from status 
            where category=%s and user_id=%s''', (cate, user_id))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return 0
    
    @classmethod
    def get_count_by_cate(cls, cate, user_id):
        cursor = db_conn.cursor()
        cursor.execute('''select count(1) from status 
            where category=%s and user_id=%s''', (cate, user_id))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return 0

    def get_data(self):
        if self.category == config.CATE_DOUBAN_MINIBLOG:
            return DoubanMiniBlogData(self.raw)
        elif self.category == config.CATE_DOUBAN_NOTE:
            return DoubanNoteData(self.raw)
        elif self.category == config.CATE_SINA_STATUS:
            return SinaWeiboStatusData(self.raw)
        else:
            return None

## Sycktask: 用户添加的同步任务
class SyncTask(object):
    kv_db_key_task = '/synctask/%s'
    kind = config.K_SYNCTASK

    def __init__(self, id, category, user_id, time):
        self.id = str(id)
        self.category = category
        self.user_id = str(user_id)
        self.time = time

    def __repr__(self):
        return "<SyncTask id=%s, user_id=%s, cate=%s>" \
            %(self.id, self.user_id, self.category)
    __str__ = __repr__

    @classmethod
    def add(cls, category, user_id):
        task = None
        cursor = db_conn.cursor()
        try:
            cursor.execute("""insert into sync_task
                    (category, user_id) values (%s,%s)""",
                    (category, user_id))
            db_conn.commit()
            task_id = cursor.lastrowid
            task = cls.get(task_id)
        except IntegrityError:
            db_conn.rollback()
        finally:
            cursor.close()

        return task

    @classmethod
    def get(cls, id):
        task = None
        cursor = db_conn.cursor()
        cursor.execute("""select category,user_id,time from sync_task
                where id=%s limit 1""", id) 
        row = cursor.fetchone()
        if row:
            task = cls(id, *row)
        cursor.close()

        return task
    
    @classmethod
    def get_ids(cls):
        cursor = db_conn.cursor()
        cursor.execute("""select id from sync_task""") 
        r = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return r
    
    @classmethod
    def gets(cls, ids):
        return [cls.get(x) for x in ids]

    @classmethod
    def gets_by_user(cls, user):
        cursor = db_conn.cursor()
        cursor.execute("""select id from sync_task where user_id = %s""", user.id)
        rows = cursor.fetchall()
        cursor.close()
        return [cls.get(row[0] )for row in rows]

    @classmethod
    def gets_by_user_and_cate(cls,user,cate):
        tasks = cls.gets_by_user(user)
        return [x for x in tasks if str(x.category) == cate]

    def remove(self):
        cursor = db_conn.cursor()
        cursor.execute("""delete from sync_task
                where id=%s""", self.id) 
        db_conn.commit()
        cursor.close()
        return None
    
    def get_detail(self):
        k = self.__class__.kv_db_key_task % self.id
        d = redis_conn.get(k)
        d = json_decode(d) if d else {}
        return d

    def update_detail(self, detail):
        k = self.__class__.kv_db_key_task % self.id
        redis_conn.set(k, json_encode(detail))
        return self.get_detail()

class TaskQueue(object):
    kind = config.K_TASKQUEUE

    def __init__(self, id, task_id, task_kind, time):
        self.id = str(id)
        self.task_id = str(task_id)
        self.task_kind = task_kind
        self.time = time

    @classmethod
    def add(cls, task_id, task_kind):
        task = None
        cursor = db_conn.cursor()
        try:
            cursor.execute("""insert into task_queue
                    (task_id, task_kind) values (%s,%s)""",
                    (task_id, task_kind))
            db_conn.commit()
            task = cls.get(cursor.lastrowid)
        except IntegrityError:
            db_conn.rollback()
        finally:
            cursor.close()

        return task

    @classmethod
    def get(cls, id):
        task = None
        cursor = db_conn.cursor()
        cursor.execute("""select id, task_id, task_kind, time from task_queue
                where id=%s limit 1""", id) 
        row = cursor.fetchone()
        if row:
            task = cls(*row)
        cursor.close()

        return task
    
    @classmethod
    def get_all_ids(cls):
        cursor = db_conn.cursor()
        cursor.execute("""select id from task_queue order by time""") 
        r = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return r

    def remove(self):
        cursor = db_conn.cursor()
        cursor.execute("""delete from task_queue
                where id=%s""", self.id) 
        db_conn.commit()
        cursor.close()
        

