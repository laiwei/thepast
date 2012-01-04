#-*- coding:utf-8 -*-

import config 
from .model.user import User

def auth_user_from_session(session_):
    user = None
    if config.SITE_COOKIE in session_:
        cookies = session_[config.SITE_COOKIE]
        user_id, session_id = cookies.split(":")
        _user = User.get(user_id)
        if _user and _user.session_id == session_id:
            user = _user

    return user 

def set_user_cookie(user, session_):
    session_[config.SITE_COOKIE] = "%s:%s" % (user.id, user.session_id)


