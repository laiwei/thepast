#-*- coding:utf-8 -*-
import os
from flask import g, session, request, send_from_directory, \
    redirect, url_for, abort, render_template, flash

import config
from past.corelib import auth_user_from_session, set_user_cookie
from past.utils.escape import json_encode, json_decode
from past.model.user import User, UserAlias, OAuth2Token
from past.model.status import SyncTask
from past.oauth_login import DoubanLogin, OAuthLoginError
import api_client

from past import app

@app.before_request
def before_request():
    g.user = auth_user_from_session(session)
    print '--before: g.user is ', g.user, 'id(g) is ', id(g), \
            'request is ', request

@app.teardown_request
def teardown_request(exception):
    print '--teardown: g.user is ', g.user, 'id(g) is ', id(g), 

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
        "favicon.ico", mimetype="image/vnd.microsoft.icon")

@app.route("/")
def index():
    return render_template("timeline.html")

@app.route("/user/<uid>")
def user(uid):
    u = User.get(uid)
    print '--------------user:', u, u.name, request
    return u.name

@app.route("/signin")
def signin():
    return "signin"

@app.route("/connect/", defaults={"provider": config.OPENID_DOUBAN})
@app.route("/connect/<provider>")
def connect(provider):
    if g.user:
        return "Hi, %s, you have already login" %g.user.name

    d = config.APIKEY_DICT.get(provider)
    douban = DoubanLogin(d['key'], d['secret'], d['redirect_uri'])
    login_uri = douban.get_login_uri()
    print '----login uri:', login_uri
    return redirect(login_uri)

@app.route("/connect/<provider>/callback")
def connect_callback(provider):
    code = request.args.get("code")
    if not code:
        abort(401)

    d = config.APIKEY_DICT.get(provider)
    douban = DoubanLogin(d['key'], d['secret'], d['redirect_uri'])
    try:
        token_dict = douban.get_access_token(code)
    except OAuthLoginError, e:
        abort(401, e.msg)
    
    douban_user_id = token_dict.get("douban_user_id")
    if not douban_user_id:
        abort(401, "no_douban_user_id")

    ua = UserAlias.get(config.OPENID_TYPE_DICT[config.OPENID_DOUBAN],
            douban_user_id)
    if not ua:
        ua = UserAlias.create_new_user(
                config.OPENID_TYPE_DICT[config.OPENID_DOUBAN], 
                douban_user_id, douban_user_id)   
    if not ua:
        abort(401)

    OAuth2Token.add(ua.id, token_dict.get("access_token"), 
            token_dict.get("refresh_token"))
    user_info = api_client.Douban(ua.alias, token_dict.get("access_token")).get_me() 
    
    g.user = User.get(ua.user_id)
    set_user_cookie(g.user, session)
    
    return g.user.name + json_encode(user_info)


@app.route("/sync/<provider>/<cates>")
def sync(provider,cates):
    if provider not in ('douban', 'wordpress','weibo'):
        abort(401, "暂时不支持其他服务")
    cates = cates.split("|")

    if provider == 'douban':
        return sync_douban(cates)

    elif provider == 'wordpress':
        pass

    elif provider == 'weibo':
        pass

def sync_douban(cates):
    if not (cates and isinstance(cates, list)):
        return "no cates"

    if not g.user:
        return redirect("/connect/douban")
    
    uas = UserAlias.gets_by_user_id(g.user.id)
    r = filter(lambda x: x.type == config.OPENID_TYPE_DICT[config.OPENID_DOUBAN], uas)
    user_alias = r and r[0]
    
    if not user_alias:
        return redirect("/connect/douban")

    token = OAuth2Token.get(user_alias.id)   
    
    if not token:
        return redirect("/connect/douban")
    
    if cates is None:
        SyncTask.add(config.CATE_DOUBAN_STATUS, g.user.id)
        SyncTask.add(config.CATE_DOUBAN_NOTE, g.user.id)
        SyncTask.add(config.CATE_DOUBAN_MINIBLOG, g.user.id)

    cates = filter(lambda x: x in config.CATE_LIST, cates)
    for c in cates:
        SyncTask.add(c, g.user.id)
    
    flash("good, douban sync task add succ...")
    return redirect("/connect")
