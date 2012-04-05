#-*- coding:utf-8 -*-

from functools import wraps
from flask import g, flash, redirect

def require_login(redir=None):
    def _(f):
        @wraps(f)
        def __(*a, **kw):
            if not g.user:
                flash(u"为了保护用户的隐私，请先登录后再查看^^", "tip")
                return redirect("/home?redir=%s" %redir)
            return f(*a, **kw)
        return __
    return _

