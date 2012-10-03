#-*- coding:utf-8 -*-

from past import config 
from past.utils import randbytes

from past.corelib.cache import cache

def auth_user_from_session(session_):
    user = None
    if config.SITE_COOKIE in session_:
        cookies = session_[config.SITE_COOKIE]
        user_id, session_id = cookies.split(":")
        ## 这里存在循环引用，所以放到函数内部，长远看这个函数不应该放在corelib中
        from past.model.user import User
        _user = User.get(user_id)
        if _user and _user.session_id == session_id:
            user = _user

    return user 

def set_user_cookie(user, session_):
    if not user:
        return None
    session_id = user.session_id if user.session_id else randbytes(8)
    user.update_session(session_id)
    session_[config.SITE_COOKIE] = "%s:%s" % (user.id, session_id)

def logout_user(user):
    if not user:
        return 
    user.clear_session()

def category2provider(cate):
    if cate < 200:
        return config.OPENID_DOUBAN
    elif cate < 300:
        return config.OPENID_SINA
    elif cate < 400:
        return config.OPENID_WORDPRESS
    elif cate < 500:
        return config.OPENID_TWITTER
    elif cate < 600:
        return config.OPENID_QQ
    elif cate < 700:
        return config.OPENID_THEPAST
    elif cate < 800:
        return config.OPENID_RENREN
    elif cate < 900:
        return config.OPENID_INSTAGRAM
    else:
        return None

