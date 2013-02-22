#-*- coding:utf-8 -*-
from flask import g, session, request, \
    redirect, url_for, abort, render_template, flash

from past import app
from past import config
from past.store import db_conn
from past.model.user import User, UserAlias
from past.corelib import auth_user_from_session

import settings, pdf_view, note, user_past, views

@app.before_request
def before_request():
    g.config = config
    g.user = auth_user_from_session(session)
    #g.user = User.get(2)
    g.user_alias = UserAlias.gets_by_user_id(g.user.id) if g.user else None

    if request.method == 'POST':
        try:
            g.start = int(request.form.get('start', 0))
        except ValueError:
            g.start = 0
        try:
            g.count = int(request.form.get('count', 24))
        except ValueError:
            g.count = 0
        g.cate = request.form.get("cate", "")
    else:
        try:
            g.start = int(request.args.get('start', 0))
        except ValueError:
            g.start = 0
        try:
            g.count = int(request.args.get('count', 24))
        except ValueError:
            g.count = 0
        g.cate = request.args.get("cate", "")
    g.cate = int(g.cate) if g.cate.isdigit() else ""
        
    if g.user:
        g.binds = [ua.type for ua in g.user.get_alias()]
        unbinded = list(set(config.OPENID_TYPE_DICT.values()) - 
                set(g.binds) - set([config.OPENID_TYPE_DICT[config.OPENID_THEPAST]]))
        tmp = {}
        for k, v in config.OPENID_TYPE_DICT.items():
            tmp[v] = k
        g.unbinded = [[x, tmp[x], config.OPENID_TYPE_NAME_DICT[x]] for x in unbinded]

        expired_providers = []
        for t in [ua.type for ua in g.user.get_alias()]:
            p = g.user.get_thirdparty_profile(t)
            if p and p.get("expired"):
                _ = [t, config.OPENID_TYPE_DICT_REVERSE.get(t), config.OPENID_TYPE_NAME_DICT.get(t, "")]
                expired_providers.append(_)
        g.expired = expired_providers
        if expired_providers:
            msg = " ".join([x[-1] for x in expired_providers])
            flash(u"你的 %s 授权已经过期了，会影响数据同步，你可以重新授权 :)" % msg, "tip")
    else:
        g.unbinded = None

@app.teardown_request
def teardown_request(exception):
    #http://stackoverflow.com/questions/9318347/why-are-some-mysql-connections-selecting-old-data-the-mysql-database-after-a-del
    db_conn.commit()
