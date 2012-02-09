#-*- coding:utf-8 -*-
import os
from flask import g, session, request, send_from_directory, \
    redirect, url_for, abort, render_template, flash

import config
from past.corelib import auth_user_from_session, set_user_cookie, \
    logout_user, category2provider
from past.utils.escape import json_encode, json_decode
from past.model.user import User, UserAlias, OAuth2Token
from past.model.status import SyncTask, Status
from past.oauth_login import DoubanLogin, SinaLogin, OAuthLoginError, TwitterOAuthLogin
import api_client

from past import app

@app.before_request
def before_request():
    g.user = auth_user_from_session(session)
    #g.user = User.get(2)
    if g.user:
        g.user_alias = UserAlias.gets_by_user_id(g.user.id)
    else:
        g.user_alias = None
    g.start = int(request.args.get('start', 0))
    g.count = int(request.args.get('count', 20))

@app.teardown_request
def teardown_request(exception):
    pass

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
        "favicon.ico", mimetype="image/vnd.microsoft.icon")

@app.route("/")
def index():
    if not g.user:
        return redirect(url_for("login"))

    cate = request.args.get("cate", None)
    ids = Status.get_ids(user_id=g.user.id, start=g.start, limit=g.count, cate=cate)
    status_list = Status.gets(ids)
    return render_template("timeline.html", user=g.user, status_list=status_list, config=config)

@app.route("/user/<uid>")
def user(uid):
    u = User.get(uid)
    if not u:
        abort(404, "no such user")

    if g.user and g.user.id == u.id:
        return redirect(url_for("index"))
    
    #TODO:增加可否查看其他用户的权限检查
    cate = request.args.get("cate", None)
    ids = Status.get_ids(user_id=u.id, start=g.start, limit=g.count, cate=cate)
    status_list = Status.gets(ids)
    return render_template("timeline.html", user=u, status_list=status_list, config=config)


@app.route("/settings/profile")
def profile():
    if not g.user:
        return redirect("/login")

    u = g.user
    sync_tasks = SyncTask.gets_by_user(u)
    my_sync_cates = [x.category for x in sync_tasks]
    site_homepage_list = []
    for ua in g.user_alias:
        if ua.type == config.OPENID_TYPE_DICT[config.OPENID_DOUBAN]:
            site_homepage_list.append({'site':u'豆瓣', 'homepage':'http://www.douban.com/people/%s' %ua.alias})
        elif ua.type == config.OPENID_TYPE_DICT[config.OPENID_SINA]:
            site_homepage_list.append({'site':u'新浪微博', 'homepage':'http://www.weibo.com/%s' %ua.alias})
        elif ua.type == config.OPENID_TYPE_DICT[config.OPENID_TWITTER]:
            site_homepage_list.append({'site':u'twitter', 'homepage':'http://www.twitter.com/%s' %ua.alias})
    return render_template("profile.html", user=u, 
            my_sync_cates = my_sync_cates, site_homepage_list=site_homepage_list, config=config)

@app.route("/logout")
def logout():
    if not g.user:
        return "you are not login"
    r = logout_user(g.user)
    return "logout succ"

#TODO
@app.route("/login")
def login():
    if g.user:
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/connect/", defaults={"provider": config.OPENID_DOUBAN})
@app.route("/connect/<provider>")
def connect(provider):
    d = config.APIKEY_DICT.get(provider)
    login_service = None
    if provider == config.OPENID_DOUBAN:
        login_service = DoubanLogin(d['key'], d['secret'], d['redirect_uri'])
    elif provider == config.OPENID_SINA:
        login_service = SinaLogin(d['key'], d['secret'], d['redirect_uri'])
    elif provider == config.OPENID_TWITTER:
        login_service = TwitterOAuthLogin(d['key'], d['secret'], d['redirect_uri'])
    try:
        login_uri = login_service.get_login_uri()
    except OAuthLoginError, e:
        return "auth error:%s" % e

    if provider == config.OPENID_TWITTER:
        login_service.save_request_token_to_session(session)
        
    return redirect(login_uri)

## 这里其实是所有的登陆入口
@app.route("/connect/<provider>/callback")
def connect_callback(provider):
    code = request.args.get("code")

    d = config.APIKEY_DICT.get(provider)
    login_service = None
    if provider == config.OPENID_DOUBAN:
        openid_type = config.OPENID_TYPE_DICT[config.OPENID_DOUBAN]
        login_service = DoubanLogin(d['key'], d['secret'], d['redirect_uri'])
    elif provider == config.OPENID_SINA:
        openid_type = config.OPENID_TYPE_DICT[config.OPENID_SINA]
        login_service = SinaLogin(d['key'], d['secret'], d['redirect_uri'])
    elif provider == config.OPENID_TWITTER:
        user = _twitter_callback(request)
        print '---debug, twitter callback, user:',user
        if user:
            return redirect(url_for('index'))
        else:
            return "connect fail"

    try:
        token_dict = login_service.get_access_token(code)
    except OAuthLoginError, e:
        abort(401, e.msg)

    if not ( token_dict and token_dict.get("access_token") ):
        abort(401, "no_access_token")
    try:
        user_info = login_service.get_user_info(
            token_dict.get("access_token"), token_dict.get("uid"))
    except OAuthLoginError, e:
        abort(401, e.msg)
    
    user = _save_user_and_token(token_dict, user_info, openid_type)
    if user:
        return redirect(url_for('index'))
    else:
        return "connect fail"

@app.route("/sync/<cates>", methods=["GET", "POST"])
def sync(cates):
    cates = cates.split("|")
    if not (cates and isinstance(cates, list)):
        return "no cates"

    cates = filter(lambda x: x in [str(y) for y in config.CATE_LIST], cates)
    if not cates:
        abort(400, "not support such cates")

    provider = category2provider(int(cates[0]))
    redir = "/connect/%s" % provider

    if not g.user:
        print '--- no g.user...'
        return redirect(redir)

    if request.form.get("remove"):
        for c in cates:
            r = SyncTask.gets_by_user_and_cate(g.user, str(c))
            for x in r:
                x.remove()
        return json_encode({'ok':'true'})

    uas = UserAlias.gets_by_user_id(g.user.id)
    r = filter(lambda x: x.type == config.OPENID_TYPE_DICT[provider], uas)
    user_alias = r and r[0]
    
    if not user_alias:
        print '--- no user_alias...'
        return json_encode({'ok':'false', 'redir':redir})

    token = OAuth2Token.get(user_alias.id)   
    
    if not token:
        print '--- no token...'
        return json_encode({'ok':'false', 'redir':redir})

    for c in cates:
        SyncTask.add(c, g.user.id)
    
    return json_encode({'ok':'true'})

def _twitter_callback(request):
    d = config.APIKEY_DICT.get(config.OPENID_TWITTER)
    openid_type = config.OPENID_TYPE_DICT[config.OPENID_TWITTER]
    login_service = TwitterOAuthLogin(d['key'], d['secret'], d['redirect_uri'])

    ## from twitter
    code = request.args.get("oauth_code") ## FIXME no use
    verifier = request.args.get("oauth_verifier")
    
    ## from session
    request_token = login_service.get_request_token_from_session(session)
    
    ## set the authorized request_token to OAuthHandle
    login_service.auth.set_request_token(request_token.get("key"), 
            request_token.get("secret"))

    ## get access_token
    try:
        token_dict = login_service.get_access_token(verifier)
    except OAuthLoginError, e:
        abort(401, e.msg)

    api = login_service.api(token_dict.get("access_token"), 
            token_dict.get("access_token_secret"))
    user_info = login_service.get_user_info(api)
    
    user = _save_user_and_token(token_dict, user_info, openid_type)
    return user
    
## 保存用户信息到数据库，并保存token
def _save_user_and_token(token_dict, user_info, openid_type):
    print '----saving',token_dict, user_info, openid_type
    ua = UserAlias.get(openid_type, user_info.get_user_id())
    if not ua:
        if not g.user:
            ua = UserAlias.create_new_user(openid_type,
                    user_info.get_user_id(), user_info.get_nickname())
        else:
            ua = UserAlias.bind_to_exists_user(g.user, 
                    openid_type, user_info.get_user_id())
    if not ua:
        return None

    ##设置个人资料（头像等等）
    u = User.get(ua.user_id)
    u.set_avatar_url(user_info.get_avatar())
    u.set_icon_url(user_info.get_icon())

    ##保存access token
    if openid_type == config.OPENID_TYPE_DICT[config.OPENID_TWITTER]:
        OAuth2Token.add(ua.id, token_dict.get("access_token"), 
                token_dict.get("access_token_secret", ""))
    else:
        OAuth2Token.add(ua.id, token_dict.get("access_token"), 
                token_dict.get("refresh_token", ""))

    ##set cookie，保持登录状态
    if not g.user:
        g.user = User.get(ua.user_id)
        set_user_cookie(g.user, session)
    
    return g.user


