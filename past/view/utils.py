#-*- coding:utf-8 -*-

from functools import wraps
from flask import g, flash, redirect, url_for, abort

from past.model.user import User
from past.model.note import Note
from past import consts
from past import config

def require_login(msg="", redir=""):
    def _(f):
        @wraps(f)
        def __(*a, **kw):
            if not g.user:
                flash(msg and msg.decode("utf8") or u"为了保护用户的隐私，请先登录^^", "tip")
                return redirect(redir or "/home")
            return f(*a, **kw)
        return __
    return _

def check_access_user(user):
    user_privacy = user.get_profile_item('user_privacy')
    if user_privacy == consts.USER_PRIVACY_PRIVATE and not (g.user and g.user.id == user.id):
        return (403, "由于该用户设置了仅自己可见的权限，所以，我们就看不到了")
    elif user_privacy == consts.USER_PRIVACY_THEPAST and not g.user:
        return (403, "由于用户设置了仅登录用户可见的权限，所以，需要登录后再看")

def check_access_note(note):
    if note.privacy == consts.STATUS_PRIVACY_PRIVATE and not (g.user and g.user.id == note.user_id):
        return (403, "由于该日记设置了仅自己可见的权限，所以，我们就看不到了")
    elif note.privacy == consts.STATUS_PRIVACY_THEPAST and not g.user:
        return (403, "由于该日记设置了仅登录用户可见的权限，所以，需要登录后再看")

## 把status_list构造为month，day的层级结构
def statuses_timelize(status_list):

    hashed = {}
    for s in status_list:
        hash_s = hash(s)
        if hash_s not in hashed:
            hashed[hash_s] = RepeatedStatus(s)
        else:
            hashed[hash_s].status_list.append(s)
    
    return sorted(hashed.values(), key=lambda x:x.create_time, reverse=True)

class RepeatedStatus(object):
    def __init__(self, status):
        self.create_time = status.create_time
        self.status_list = [status]

def get_sync_list(user):
    print '------user:',user
    user_binded_providers = [ua.type for ua in user.get_alias() if ua.type in config.CAN_SHARED_OPENID_TYPE]

    sync_list = []
    for t in user_binded_providers:
        p = user.get_thirdparty_profile(t)
        if p and p.get("share") == "Y":
            sync_list.append([t, "Y"])
        else:
            sync_list.append([t, "N"])
    return sync_list
