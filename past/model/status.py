#-*- coding:utf-8 -*-

import datetime
from MySQLdb import IntegrityError
from past import config
from past.utils.escape import json_encode, json_decode, linkify, MyHTMLParser
from past.utils.logger import logging
from past.store import connect_redis, connect_db
from past.model.user import UserAlias

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
        self.title = title and linkify(title) or ""
        self.text = json_decode(redis_conn.get(
                self.__class__.STATUS_REDIS_KEY % self.id))
        self.text = MyHTMLParser.parse(self.text, preserve=['img', 'a'])
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
        return [x[0] for x in rows]
    
    @classmethod
    def gets(cls, ids):
        return [cls.get(x) for x in ids]

    @classmethod
    def get_max_origin_id(cls, cate):
        cursor = db_conn.cursor()
        cursor.execute('''select max(origin_id) from status 
            where category=%s''', (cate,))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return 0

    @classmethod
    def get_min_origin_id(cls, cate):
        cursor = db_conn.cursor()
        cursor.execute('''select min(origin_id) from status 
            where category=%s''', (cate,))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return 0
    
    @classmethod
    def get_count_by_cate(cls, cate):
        cursor = db_conn.cursor()
        cursor.execute('''select count(1) from status 
            where category=%s''', (cate,))
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

## User数据接口 
class AbsUserData(object):

    def __init__(self, data):
        self.data = data
        if isinstance(data, basestring):
            self.data = json_decode(data)

    def get_user_id(self):
        raise NotImplementedError

    def get_uid(self):
        raise NotImplementedError

    def get_nickname(self):
        raise NotImplementedError

    def get_intro(self):
        raise NotImplementedError

    def get_signature(self):
        raise NotImplementedError

    def get_avatar(self):
        raise NotImplementedError

    def get_icon(self):
        raise NotImplementedError
    
## 豆瓣user数据接口
class DoubanUser(AbsUserData):
    def __init__(self, data):
        super(DoubanUser, self).__init__(data)

    def get_user_id(self):
        id_ = self.data.get("id", {}).get("$t")
        if id_:
            return (id_.rstrip("/").split("/"))[-1]
        return None

    def get_uid(self):
        return self.data.get("uid", {}).get("$t")

    def get_nickname(self):
        return self.data.get("title", {}).get("$t")

    def get_intro(self):
        return self.data.get("content", {}).get("$t")

    def get_signature(self):
        return self.data.get("signature", {}).get("$t")

    def get_avatar(self):
        icon = self.get_icon()
        user_id = self.get_user_id()

        return icon.replace(user_id, "l%s" % user_id)

    def get_icon(self):
        return self.data.get("link")[2].get("@href", "")
        

## 新浪微博user数据接口
class SinaWeiboUser(AbsUserData):

    def __init__(self, data):
        super(SinaWeiboUser, self).__init__(data)

    def get_user_id(self):
        return self.data.get("idstr","")

    def get_uid(self):
        return self.data.get("domain", "")

    def get_nickname(self):
        return self.data.get("screen_name", "")

    def get_intro(self):
        return self.data.get("description", "")

    def get_signature(self):
        return ""

    def get_avatar(self):
        return self.data.get("avatar_large", "")

    def get_icon(self):
        return self.data.gete("profile_image_url", "")

## 第三方数据接口
class AbsData(object):
    
    def __init__(self, site, category, data):
        self.site = site
        self.category = category
        self.data = data
        if isinstance(data, basestring):
            self.data = json_decode(data)

    def get_data(self):
        return self.data
    
    def get_origin_id(self):
        raise NotImplementedError

    def get_create_time(self):
        raise NotImplementedError

    def get_title(self):
        raise NotImplementedError

    def get_content(self):
        raise NotImplementedError

    def get_retweeted_status(self):
        raise NotImplementedError

    def get_user(self):
        raise NotImplementedError

class DoubanData(AbsData):
    
    def __init__(self, category, data):
        super(DoubanData, self).__init__( 
                config.OPENID_TYPE_DICT[config.OPENID_DOUBAN], category, data)

# 日记
class DoubanNoteData(DoubanData):
    def __init__(self, data):
        super(DoubanNoteData, self).__init__(
                config.CATE_DOUBAN_NOTE, data)

    def get_origin_id(self):
        id_ = self.data.get("id", {}).get("$t")
        if id_:
            return (id_.rstrip("/").split("/"))[-1]
        return None

    def get_create_time(self):
        return self.data.get("published",{}).get("$t")

    def get_title(self):
        return self.data.get("title", {}).get("$t")

    def get_content(self):
        return self.data.get("content", {}).get("$t")

# 广播
class DoubanMiniBlogData(DoubanData):
    def __init__(self, data):
        super(DoubanMiniBlogData, self).__init__(
                config.CATE_DOUBAN_MINIBLOG, data)

    def get_origin_id(self):
        id_ = self.data.get("id", {}).get("$t")
        if id_:
            return (id_.rstrip("/").split("/"))[-1]
        return None

    def get_create_time(self):
        return self.data.get("published",{}).get("$t")

    def get_title(self):
        return self.data.get("title", {}).get("$t")

    def get_content(self):
        return self.data.get("content", {}).get("$t")
    
    def get_links(self):
        links = {}
        _links = self.data.get("link", [])
        for x in _links:
            rel = x.get("@rel")
            links[rel] = x.get("@href")
        return links

# 相册 
class DoubanPhotoData(DoubanData):
    def __init__(self, data):
        super(DoubanPhotoData, self).__init__(
                config.CATE_DOUBAN_PHOTO, data)

    def get_origin_id(self):
        id_ = self.data.get("id", {}).get("$t")
        if id_:
            return (id_.rstrip("/").split("/"))[-1]
        return None

    def get_create_time(self):
        return self.data.get("published",{}).get("$t")

    def get_title(self):
        return self.data.get("title", {}).get("$t")

    def get_content(self):
        return self.data.get("content", {}).get("$t")

    def get_large_img_src(self):
        links = self.data.get("link", [])
        for x in links:
            if x.get("@rel") == "image":
                return x.get("@href")
    
    def get_thumb_img_src(self):
        links = self.data.get("link", [])
        for x in links:
            if x.get("@rel") == "thumb":
                return x.get("@href")

# 我说 
class DoubanStatusData(DoubanData):
    
    def __init__(self, data):
        super(DoubanStatusData, self).__init__(
                config.CATE_DOUBAN_STATUS, data)

    def get_origin_id(self):
        return self.data.get("id")

    def get_create_time(self):
        return self.data.get("created_at")

    def get_title(self):
        return ""

    def get_content(self):
        return self.data.get("text")

    def get_attachments(self):
        attachs =  self.data.get("attachments")
        return [DoubanStatusAttachment(x) for x in attachs]


class DoubanStatusAttachment(object):
    
    def __init__(self, data):
        self.data = data

    def get_title(self):
        return self.data.get("title")

    def get_href(self):
        return self.data.get("expaned_href")

    def get_caption(self):
        return self.data.get("caption")

    def get_description(self):
        return self.data.get("discription")

    def get_media(self):
        medias = self.data.get("media")
        return [DoubanStatusAttachmentMedia(x) for x in medias]

    def get_props(self):
        props = self.data.get("properties", {}) 
        return props

class DoubanStatusAttachmentMedia(object):
    
    def __init__(self, data):
        self.data = data

    def get_type(self):
        return self.data.get("type")
    
    def get_media_src(self):
        return self.data.get("src")

    def get_href(self):
        return self.data.get("href")

    def get_size(self):
        return self.data.get("size")

    ## just for music
    def get_title(self):
        return self.data.get("title")

    ##-- just for flash
    def get_imgsrc(self):
        return self.data.get("imgsrc")


class SinaWeiboData(AbsData):
    
    def __init__(self, category, data):
        super(SinaWeiboData, self).__init__( 
                config.OPENID_TYPE_DICT[config.OPENID_SINA], category, data)

class SinaWeiboStatusData(SinaWeiboData):
    def __init__(self, data):
        super(SinaWeiboStatusData, self).__init__(
                config.CATE_SINA_STATUS, data)
    
    def get_origin_id(self):
        return self.data.get("idstr", "")

    def get_create_time(self):
        t = self.data.get("created_at", "")
        return datetime.datetime.strptime(t, "%a %b %d %H:%M:%S +0800 %Y")

    def get_title(self):
        return ""

    def get_content(self):
        return self.data.get("text", "") 
    
    def get_retweeted_status(self):
        re = self.data.get("retweeted_status")
        if re:
            return SinaWeiboStatusData(re)

    def get_user(self):
        return SinaWeiboUser(self.data.get("user"))

    def get_origin_pic(self):
        return self.data.get("original_pic", "")

    def get_thumbnail_pic(self):
        return self.data.get("thumbnail_pic", "")

    def get_middle_pic(self):
        return self.data.get("bmiddle_pic", "")

## Sycktask: 用户添加的同步任务
class SyncTask(object):
    kv_db_key_task = '/synctask/%s'

    def __init__(self, id, category, user_id, time):
        self.id = str(id)
        self.category = category
        self.user_id = str(user_id)
        self.time = time

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
