#-*- coding:utf-8 -*-

import datetime
import hashlib
import re
from MySQLdb import IntegrityError

from past.utils.escape import json_encode, json_decode, clear_html_element
from past.utils.logger import logging
from past.store import mc, db_conn
from past.corelib.cache import cache, pcache, HALF_HOUR
from .user import UserAlias, User
from .note import Note
from .data import DoubanMiniBlogData, DoubanNoteData, DoubanStatusData, \
        SinaWeiboStatusData, QQWeiboStatusData, TwitterStatusData,\
        WordpressData, ThepastNoteData, RenrenStatusData, RenrenBlogData, \
        RenrenAlbumData, RenrenPhotoData, InstagramStatusData
from .kv import RawStatus
from past import config
from past import consts

log = logging.getLogger(__file__)

#TODO:refactor,暴露在外面的接口为Status
#把Data相关的都应该隐藏起来,不允许外部import

class Status(object):
    
    def __init__(self, id, user_id, origin_id, 
            create_time, site, category, title=""):
        self.id = str(id)
        self.user_id = str(user_id)
        self.origin_id = str(origin_id)
        self.create_time = create_time
        self.site = site
        self.category = category
        self.title = title
        _data_obj = self.get_data()
        ##对于140字以内的消息，summary和text相同；对于wordpress等长文，summary只是摘要，text为全文
        ##summary当作属性来，可以缓存在mc中，text太大了，作为一个method
        self.summary = _data_obj and _data_obj.get_summary() or ""
        if self.site == config.OPENID_TYPE_DICT[config.OPENID_TWITTER]:
            self.create_time += datetime.timedelta(seconds=8*3600)
        
        self._bare_text = self._generate_bare_text()

    def __repr__(self):
        return "<Status id=%s, user_id=%s, origin_id=%s, cate=%s>" \
            %(self.id, self.user_id, self.origin_id, self.category)
    __str__ = __repr__

    def __eq__(self, other):
        ##同一用户，在一天之内发表的，相似的内容，认为是重复的^^, 
        ##对于23点和凌晨1点这种跨天的没有考虑
        ##FIXME:abs(self.create_time - other.create_time) <= datetime.timedelta(1) 
        if self.user_id == other.user_id \
                and abs(self.create_time.day - other.create_time.day) == 0 \
                and  self._bare_text == other._bare_text:
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        if self.category == config.CATE_QQWEIBO_STATUS and self.get_retweeted_data():
            return int(self.id)
        if (self.category == config.CATE_SINA_STATUS or self.category == config.CATE_DOUBAN_STATUS) \
                and self.get_retweeted_data():
            return int(self.id)
        if self.category == config.CATE_DOUBAN_STATUS and \
                self.get_data() and self.get_data().get_attachments():
            return int(self.id)
        if self.category == config.CATE_THEPAST_NOTE:
            return int(self.id)
        if self.category == config.CATE_RENREN_STATUS or \
                self.category == config.CATE_RENREN_BLOG or \
                self.category == config.CATE_RENREN_ALBUM or \
                self.category == config.CATE_RENREN_PHOTO or \
                self.category == config.CATE_INSTAGRAM_STATUS:
            return int(self.id)
        s = u"%s%s%s" % (self.user_id, self._bare_text, self.create_time.day)
        d = hashlib.md5()
        d.update(s.encode("utf8"))
        return int(d.hexdigest(),16)
        
    def _generate_bare_text(self, offset=140):
        bare_text = self.summary[:offset]
        bare_text = clear_html_element(bare_text).replace(u"《", "").replace(u"》", "").replace("amp;","")
        bare_text = re.sub("\s", "", bare_text)
        bare_text = re.sub("http://t.cn/[a-zA-Z0-9]+", "", bare_text)
        bare_text = re.sub("http://t.co/[a-zA-Z0-9]+", "", bare_text)
        bare_text = re.sub("http://url.cn/[a-zA-Z0-9]+", "", bare_text)
        bare_text = re.sub("http://goo.gl/[a-zA-Z0-9]+", "", bare_text)
        bare_text = re.sub("http://dou.bz/[a-zA-Z0-9]+", "", bare_text).replace(u"说：", "")
        return bare_text  

    ##TODO:这个clear_cache需要拆分
    @classmethod
    def _clear_cache(cls, user_id, status_id, cate=""):
        if status_id:
            mc.delete("status:%s" % status_id)
        if user_id:
            mc.delete("status_ids:user:%scate:" % user_id)
            if cate:
                mc.delete("status_ids:user:%scate:%s" % (user_id, cate))

    def privacy(self):
        if self.category == config.CATE_THEPAST_NOTE:
            note = Note.get(self.origin_id)
            return note and note.privacy
        else:
            return consts.STATUS_PRIVACY_PUBLIC
        
    @property
    def text(self):
        if self.category == config.CATE_THEPAST_NOTE:
            note = Note.get(self.origin_id)
            return note and note.content
        else:
            r = RawStatus.get(self.id)
            _text = r.text if r else ""
            return json_decode(_text) if _text else ""

    @property
    def raw(self):
        if self.category == config.CATE_THEPAST_NOTE:
            note = Note.get(self.origin_id)
            return note
        else:
            r = RawStatus.get(self.id)
            _raw = r.raw if r else ""
            try:
                return json_decode(_raw) if _raw else ""
            except:
                return ""
        
    @classmethod
    def add(cls, user_id, origin_id, create_time, site, category, title, 
            text=None, raw=None):
        status = None
        cursor = None
        try:
            cursor = db_conn.execute("""insert into status 
                    (user_id, origin_id, create_time, site, category, title)
                    values (%s,%s,%s,%s,%s,%s)""",
                    (user_id, origin_id, create_time, site, category, title))
            status_id = cursor.lastrowid
            if status_id > 0:
                text = json_encode(text) if text is not None else ""
                raw = json_encode(raw) if raw is not None else ""
                RawStatus.set(status_id, text, raw)
                db_conn.commit()
                status = cls.get(status_id)
        except IntegrityError:
            log.warning("add status duplicated, uniq key is %s:%s:%s, ignore..." %(origin_id, site, category))
            db_conn.rollback()
        finally:
            cls._clear_cache(user_id, None, cate=category)
            cursor and cursor.close()

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
    @cache("status:{status_id}")
    def get(cls, status_id):
        status = None
        cursor = db_conn.execute("""select user_id, origin_id, create_time, site, 
                category, title from status 
                where id=%s""", status_id)
        row = cursor.fetchone()
        if row:
            status = cls(status_id, *row)
        cursor and cursor.close()

        if status and status.category == config.CATE_THEPAST_NOTE:
            note = Note.get(status.origin_id)
            status.title = note and note.title

        return status

    @classmethod
    @pcache("status_ids:user:{user_id}cate:{cate}")
    def get_ids(cls, user_id, start=0, limit=20, cate=""):
        return cls._get_ids(user_id, start, limit, 
                order="create_time desc", cate=cate)

    @classmethod
    @pcache("status_ids_asc:user:{user_id}cate:{cate}")
    def get_ids_asc(cls, user_id, start=0, limit=20, cate=""):
        return cls._get_ids(user_id, start, limit, 
                order="create_time", cate=cate)

    @classmethod
    def _get_ids(cls, user_id, start=0, limit=20, order="create_time desc", cate=""):
        cursor = None
        if not user_id:
            return []
        if cate:
            if str(cate) == str(config.CATE_DOUBAN_NOTE):
                return []
            sql = """select id from status where user_id=%s and category=%s
                    order by """ + order + """ limit %s,%s""" 
            cursor = db_conn.execute(sql, (user_id, cate, start, limit))
        else:
            sql = """select id from status where user_id=%s and category!=%s
                    order by """ + order + """ limit %s,%s""" 
            cursor = db_conn.execute(sql, (user_id, config.CATE_DOUBAN_NOTE, start, limit))
        rows = cursor.fetchall()
        cursor and cursor.close()
        return [x[0] for x in rows]

    @classmethod
    def get_ids_by_date(cls, user_id, start_date, end_date):
        cursor = db_conn.execute('''select id from status 
                where user_id=%s and category!=%s and create_time>=%s and create_time<=%s
                order by create_time desc''',
                (user_id, config.CATE_DOUBAN_NOTE, start_date, end_date))
        rows = cursor.fetchall()
        cursor and cursor.close()
        return [x[0] for x in rows]

    @classmethod
    def gets(cls, ids):
        return [cls.get(x) for x in ids]

    @classmethod
    @cache("recent_updated_users", expire=HALF_HOUR)
    def get_recent_updated_user_ids(cls, limit=16):
        cursor = db_conn.execute('''select distinct user_id from status 
                order by create_time desc limit %s''', limit)
        rows = cursor.fetchall()
        cursor and cursor.close()
        return [row[0]for row in rows]

    @classmethod
    def get_max_origin_id(cls, cate, user_id):
        cursor = db_conn.execute('''select origin_id from status 
            where category=%s and user_id=%s 
            order by length(origin_id) desc, origin_id desc limit 1''', (cate, user_id))
        row = cursor.fetchone()
        cursor and cursor.close()
        if row:
            return row[0]
        else:
            return None

    @classmethod
    def get_min_origin_id(cls, cate, user_id):
        cursor = db_conn.execute('''select origin_id from status 
            where category=%s and user_id=%s 
            order by length(origin_id), origin_id limit 1''', (cate, user_id))
        row = cursor.fetchone()
        cursor and cursor.close()
        if row:
            return row[0]
        else:
            return None

    ## just for tecent_weibo
    @classmethod
    def get_oldest_create_time(cls, cate, user_id):
        if cate:
            cursor = db_conn.execute('''select min(create_time) from status 
                where category=%s and user_id=%s''', (cate, user_id))
        else:
            cursor = db_conn.execute('''select min(create_time) from status 
                where user_id=%s''', user_id)
        row = cursor.fetchone()
        cursor and cursor.close()
        if row:
            return row[0]
        else:
            return None
    
    @classmethod
    def get_count_by_cate(cls, cate, user_id):
        cursor = db_conn.execute('''select count(1) from status 
            where category=%s and user_id=%s''', (cate, user_id))
        row = cursor.fetchone()
        cursor and cursor.close()
        if row:
            return row[0]
        else:
            return 0

    @classmethod
    def get_count_by_user(cls, user_id):
        cursor = db_conn.execute('''select count(1) from status 
            where user_id=%s''', user_id)
        row = cursor.fetchone()
        cursor and cursor.close()
        if row:
            return row[0]
        else:
            return 0

    #TODO:每次新增第三方，需要修改这里
    def get_data(self):
        if self.category == config.CATE_DOUBAN_MINIBLOG:
            return DoubanMiniBlogData(self.raw)
        elif self.category == config.CATE_DOUBAN_NOTE:
            return DoubanNoteData(self.raw)
        elif self.category == config.CATE_SINA_STATUS:
            return SinaWeiboStatusData(self.raw)
        elif self.category == config.CATE_TWITTER_STATUS:
            return TwitterStatusData(self.raw)
        elif self.category == config.CATE_QQWEIBO_STATUS:
            return QQWeiboStatusData(self.raw)
        elif self.category == config.CATE_DOUBAN_STATUS:
            return DoubanStatusData(self.raw)
        elif self.category == config.CATE_WORDPRESS_POST:
            return WordpressData(self.raw)
        elif self.category == config.CATE_THEPAST_NOTE:
            return ThepastNoteData(self.raw)
        elif self.category == config.CATE_RENREN_STATUS:
            return RenrenStatusData(self.raw)
        elif self.category == config.CATE_RENREN_BLOG:
            return RenrenBlogData(self.raw)
        elif self.category == config.CATE_RENREN_ALBUM:
            return RenrenAlbumData(self.raw)
        elif self.category == config.CATE_RENREN_PHOTO:
            return RenrenPhotoData(self.raw)
        elif self.category == config.CATE_INSTAGRAM_STATUS:
            return InstagramStatusData(self.raw)
        else:
            return None

    def get_origin_uri(self):
        ##d是AbsData的子类实例
        d = self.get_data()
        if self.category == config.CATE_DOUBAN_MINIBLOG or \
                self.category == config.CATE_DOUBAN_STATUS:
            ua = UserAlias.get_by_user_and_type(self.user_id, 
                    config.OPENID_TYPE_DICT[config.OPENID_DOUBAN])
            if ua:
                return (config.OPENID_DOUBAN, 
                        config.DOUBAN_MINIBLOG % (ua.alias, self.origin_id))
        elif self.category == config.CATE_DOUBAN_NOTE:
            return (config.OPENID_DOUBAN, config.DOUBAN_NOTE % self.origin_id)
        elif self.category == config.CATE_SINA_STATUS:
            return (config.OPENID_SINA, "")
        elif self.category == config.CATE_TWITTER_STATUS:
            return (config.OPENID_TWITTER, d.get_origin_uri())
        elif self.category == config.CATE_QQWEIBO_STATUS:
            return (config.OPENID_QQ, config.QQWEIBO_STATUS % self.origin_id)
        elif self.category == config.CATE_WORDPRESS_POST:
            return (config.OPENID_WORDPRESS, d.get_origin_uri())
        elif self.category == config.CATE_THEPAST_NOTE:
            return (config.OPENID_THEPAST, d.get_origin_uri())
        elif self.category == config.CATE_RENREN_STATUS or \
                self.category == config.CATE_RENREN_BLOG or \
                self.category == config.CATE_RENREN_ALBUM or \
                self.category == config.CATE_RENREN_PHOTO:
            return (config.OPENID_RENREN, d.get_origin_uri())
        elif self.category == config.CATE_INSTAGRAM_STATUS:
            return (config.OPENID_INSTAGRAM, d.get_origin_uri())
        else:
            return None

    def get_retweeted_data(self):
        d = self.get_data()
        if hasattr(d, "get_retweeted_data"):
            return d.get_retweeted_data()
        return None

    def get_thepast_user(self):
        return User.get(self.user_id)


## Sycktask: 用户添加的同步任务
class SyncTask(object):
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
        cursor = None
        try:
            cursor = db_conn.execute("""insert into sync_task
                    (category, user_id) values (%s,%s)""",
                    (category, user_id))
            db_conn.commit()
            task_id = cursor.lastrowid
            task = cls.get(task_id)
        except IntegrityError:
            db_conn.rollback()
        finally:
            cursor and cursor.close()

        return task

    @classmethod
    def get(cls, id):
        task = None
        cursor = db_conn.execute("""select category,user_id,time from sync_task
                where id=%s limit 1""", id) 
        row = cursor.fetchone()
        if row:
            task = cls(id, *row)
        cursor and cursor.close()

        return task
    
    @classmethod
    def get_ids(cls):
        cursor = db_conn.execute("""select id from sync_task""") 
        r = [row[0] for row in cursor.fetchall()]
        cursor and cursor.close()
        return r
    
    @classmethod
    def gets(cls, ids):
        return [cls.get(x) for x in ids]

    @classmethod
    def gets_by_user(cls, user):
        cursor = db_conn.execute("""select id from sync_task where user_id = %s""", user.id)
        rows = cursor.fetchall()
        cursor and cursor.close()
        return [cls.get(row[0] )for row in rows]

    @classmethod
    def gets_by_user_and_cate(cls,user,cate):
        tasks = cls.gets_by_user(user)
        return [x for x in tasks if str(x.category) == cate]

    def remove(self):
        cursor = db_conn.execute("""delete from sync_task
                where id=%s""", self.id) 
        db_conn.commit()
        cursor and cursor.close()
        return None
    
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
        cursor = None
        try:
            cursor = db_conn.execute("""insert into task_queue
                    (task_id, task_kind) values (%s,%s)""",
                    (task_id, task_kind))
            db_conn.commit()
            task = cls.get(cursor.lastrowid)
        except IntegrityError:
            db_conn.rollback()
        finally:
            cursor and cursor.close()

        return task

    @classmethod
    def get(cls, id):
        task = None
        cursor = db_conn.execute("""select id, task_id, task_kind, time from task_queue
                where id=%s limit 1""", id) 
        row = cursor.fetchone()
        if row:
            task = cls(*row)
        cursor and cursor.close()

        return task
    
    @classmethod
    def get_all_ids(cls):
        cursor = db_conn.execute("""select id from task_queue order by time""") 
        r = [row[0] for row in cursor.fetchall()]
        cursor and cursor.close()
        return r

    def remove(self):
        cursor = db_conn.execute("""delete from task_queue
                where id=%s""", self.id) 
        db_conn.commit()
        cursor and cursor.close()
        
## functions
def get_all_text_by_user(user_id, limit=1000):
    text = ""
    status_ids = Status.get_ids(user_id, limit=limit)
    for s in Status.gets(status_ids):
        try:
            ##TODO:这里用的summary，是为了效率上的考虑
            _t = s.summary

            retweeted_data = s.get_retweeted_data()
            if retweeted_data:
                if isinstance(retweeted_data, basestring):
                    _t += retweeted_data
                else:
                    _t += retweeted_data.get_content()
            text += _t
        except Exception, e:
            print e
    return text

@cache("sids:{user_id}:{now}", expire=3600*24)
def get_status_ids_yesterday(user_id, now):
    s = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    e = now.strftime("%Y-%m-%d")
    ids = Status.get_ids_by_date(user_id, s, e)
    return ids

@cache("sids_today_in_history:{user_id}:{now}", expire=3600*24)
def get_status_ids_today_in_history(user_id, now):
    years = range(now.year-1, 2005, -1)
    dates = [("%s-%s" %(y,now.strftime("%m-%d")), 
        "%s-%s" %(y,(now+datetime.timedelta(days=1)).strftime("%m-%d"))) for y in years]
    ids = [Status.get_ids_by_date(user_id, d[0], d[1]) for d in dates]
    r =[]
    for x in ids:
        r.extend(x)
    return r

