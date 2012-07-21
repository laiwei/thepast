#-*- coding:utf-8 -*-

import markdown2
from MySQLdb import IntegrityError
import datetime

from past.store import db_conn, mc
from past.corelib.cache import cache, pcache, HALF_HOUR
from past.utils.escape import json_encode, json_decode
from past import consts
from past import config

class Note(object):
    
    def __init__(self, id, user_id, title, content, create_time, update_time, fmt, privacy):
        self.id = id
        self.user_id = str(user_id)
        self.title = title
        self.content = content
        self.create_time = create_time
        self.update_time = update_time
        self.fmt = fmt
        self.privacy = privacy

    @classmethod
    def _clear_cache(cls, user_id, note_id):
        if user_id:
            mc.delete("note_ids:%s" % user_id)
            mc.delete("note_ids_asc:%s" % user_id)
        if note_id:
            mc.delete("note:%s" % note_id)

    def flush_note(self):
        Note._clear_cache(None, self.id)
        return Note.get(self.id)

    @classmethod
    @cache("note:{id}")
    def get(cls, id):
        cursor = db_conn.execute('''select id, user_id, title, content, create_time, update_time, fmt, privacy 
            from note where id = %s''', id)
        row = cursor.fetchone()
        if row:
            return cls(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])

    def render_content(self):
        if self.fmt == consts.NOTE_FMT_MARKDOWN:
            return markdown2.markdown(self.content, extras=["wiki-tables", "code-friendly"])
        else:
            return self.content

    @classmethod
    def add(cls, user_id, title, content, fmt=consts.NOTE_FMT_PLAIN, privacy=consts.STATUS_PRIVACY_PUBLIC):
        cursor = None
        try:
            cursor = db_conn.execute('''insert into note (user_id, title, content, create_time, fmt, privacy) 
                    values (%s, %s, %s, %s, %s, %s)''',
                    (user_id, title, content, datetime.datetime.now(), fmt, privacy))
            db_conn.commit()

            note_id = cursor.lastrowid
            note = cls.get(note_id)
            from past.model.status import Status
            Status.add(user_id, note_id, 
                    note.create_time, config.OPENID_TYPE_DICT[config.OPENID_THEPAST], 
                    config.CATE_THEPAST_NOTE, "")
            cls._clear_cache(user_id, None)
            return note
        except IntegrityError:
            db_conn.rollback()
        finally:
            cursor and cursor.close()

    def update(self, title, content, fmt, privacy):
        if title and title != self.title or fmt and fmt != self.fmt or content and content != self.content or privacy and privacy != self.privacy:
            _fmt = fmt or self.fmt
            _title = title or self.title
            _content = content or self.content
            _privacy = privacy or self.privacy
            db_conn.execute('''update note set title = %s, content = %s, fmt = %s, privacy = %s where id = %s''', 
                    (_title, _content, _fmt, _privacy, self.id))
            db_conn.commit()
            self.flush_note()
            
            if title != self.title:
                from past.model.status import Status
                Status._clear_cache(None, self.get_status_id(), None)

    @cache("note:status_id:{self.id}")
    def get_status_id(self):
        cursor = db_conn.execute("""select id from status where origin_id = %s and category = %s""",
                (self.id, config.CATE_THEPAST_NOTE))
        row = cursor.fetchone()
        cursor and cursor.close()
        return row and row[0]
    
    @classmethod
    def delete(cls, id):
        note = cls.get(id)
        if note:
            db_conn.execute("""delete from status where id=%s""", id)
            db_conn.commit()
            cls._clear_cache(note.user_id, note.id)
        
    @classmethod
    @pcache("note_ids:user:{user_id}")
    def get_ids_by_user(cls, user_id, start, limit):
        return cls._get_ids_by_user(user_id, start, limit)

    @classmethod
    @pcache("note_ids_asc:user:{user_id}")
    def get_ids_by_user_asc(cls, user_id, start, limit):
        return cls._get_ids_by_user(user_id, start, limit, order="create_time asc")

    @classmethod
    def _get_ids_by_user(cls, user_id, start=0, limit=20, order="create_time desc"):
        sql = """select id from note where user_id=%s order by """ + order \
                + """ limit %s,%s"""
        cursor = db_conn.execute(sql, (user_id, start, limit))
        rows = cursor.fetchall()
        return [x[0] for x in  rows]

    @classmethod
    def gets(cls, ids):
        return [cls.get(x) for x in ids]
