#-*- coding:utf-8 -*-

from past.utils.escape import json_encode, json_decode
from MySQLdb import IntegrityError
from past.store import connect_redis, connect_db
from past import config

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
            print '---add status duplicated, ignore...'
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
    def gets(cls, ids):
        pass

class DoubanUser(object):
    def __init__(self, data):
        self.data = data
        if isinstance(data, basestring):
            self.data = json_decode(data)

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
        return self.data.get("created_at").encode("utf8")

    def get_title(self):
        return ""

    def get_content(self):
        return self.data.get("text").encode("utf8")

    def get_attachments(self):
        attachs =  self.data.get("attachments")
        return [DoubanStatusAttachment(x) for x in attachs]


class DoubanStatusAttachment(object):
    
    def __init__(self, data):
        self.data = data

    def get_title(self):
        return self.data.get("title").encode("utf8")

    def get_href(self):
        return self.data.get("expaned_href").encode("utf8")

    def get_caption(self):
        return self.data.get("caption").encode("utf8")

    def get_description(self):
        return self.data.get("discription").encode("utf8")

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
        return self.data.get("type").encode("utf8")
    
    def get_media_src(self):
        return self.data.get("src").encode("utf8")

    def get_href(self):
        return self.data.get("href").encode("utf8")

    def get_size(self):
        return self.data.get("size").encode("utf8")

    ## just for music
    def get_title(self):
        return self.data.get("title").encode("utf8")

    ##-- just for flash
    def get_imgsrc(self):
        return self.data.get("imgsrc").encode("utf8")


class SyncTask(object):
    kv_db_key_task = '/synctask/%s'

    def __init__(self, id, kind, user_id, time):
        self.id = str(id)
        self.kind = kind
        self.user_id = str(user_id)
        self.time = time

    @classmethod
    def add(cls, kind, user_id):
        task = None
        cursor = db_conn.cursor()
        try:
            cursor.execute("""insert into sync_task
                    (kind, user_id) values (%s,%s)""",
                    (kind, user_id))
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
        cursor.execute("""select kind,user_id,time from sync_task
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
        return [row[0] for row in cursor.fetchall()]
    
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
        print '---------------d:',d,";k:",k
        d = json_decode(d) if d else {}
        return d

    def update_detail(self, detail):
        k = self.__class__.kv_db_key_task % self.id
        redis_conn.set(k, json_encode(detail))
        return self.get_detail()
