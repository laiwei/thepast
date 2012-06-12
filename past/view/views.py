#-*- coding:utf-8 -*-
import os
import datetime

from flask import g, session, request, send_from_directory, \
    redirect, url_for, abort, render_template, flash

from past import config
from past.corelib import auth_user_from_session, set_user_cookie, \
        logout_user, category2provider
from past.utils.escape import json_encode
from past.model.user import User, UserAlias, OAuth2Token
from past.model.status import SyncTask, Status, TaskQueue, \
        get_status_ids_today_in_history, get_status_ids_yesterday
from past.oauth_login import DoubanLogin, SinaLogin, OAuthLoginError,\
        TwitterOAuthLogin, QQOAuth1Login
from past.cws.cut import get_keywords
from past import consts

from past import app

from .utils import require_login, check_access_user

@app.before_request
def before_request():
    g.user = auth_user_from_session(session)
    if g.user:
        g.user_alias = UserAlias.gets_by_user_id(g.user.id)
    else:
        g.user_alias = None

    if g.user:
        unbinded= list(set(config.OPENID_TYPE_DICT.values()) - 
                set([ua.type for ua in g.user.get_alias()]) - set([config.OPENID_TYPE_DICT[config.OPENID_THEPAST]]))
        tmp = {}
        for k,v in config.OPENID_TYPE_DICT.items():
            tmp[v] = k
        g.unbinded = [[x, tmp[x], config.OPENID_TYPE_NAME_DICT[x]] for x in unbinded]
    else:
        g.unbinded = None

    g.start = int(request.args.get('start', 0))
    g.count = int(request.args.get('count', 30))
    g.cate = request.args.get("cate", "")
    if not g.cate.isdigit():
        g.cate = ""

@app.teardown_request
def teardown_request(exception):
    pass

@app.route("/")
def index():
    return redirect(url_for("home"))

@app.route("/home")
def home():
    user_ids = Status.get_recent_updated_user_ids()
    users = filter(None, [User.get(x) for x in user_ids])
    users = [x for x in users if x.get_profile_item('user_privacy') != consts.USER_PRIVACY_PRIVATE]
    return render_template("home.html",
            users=users, config=config)

@app.route("/past")
@require_login()
def past():
    intros = [g.user.get_thirdparty_profile(x).get("intro") for x in config.OPENID_TYPE_DICT.values()]
    intros = filter(None, intros)
    
    yesterday_ids = get_status_ids_yesterday(g.user.id, 
            day=(datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"))
    status_of_yesterday = Status.gets(yesterday_ids)

    history_ids = get_status_ids_today_in_history(g.user.id, 
            day=datetime.datetime.now().strftime("%Y-%m-%d"))
    d = {}
    for s in Status.gets(history_ids):
        t = s.create_time.strftime("%Y-%m-%d")
        if d.has_key(t):
            d[t].append(s)
        else:
            d[t] = [s]
    status_of_today_in_history = d
    from past.consts import YESTERDAY

    return render_template("past.html", **locals())

@app.route("/post/<id>")
def post(id):
    status = Status.get(id)
    if not status:
        abort(404, "访问的文章不存在^^")
    else:
        user = User.get(status.user_id)
        if user and not check_access_user(user):
            if status.category == config.CATE_THEPAST_NOTE:
                return redirect("/note/%s" % status.origin_id)
            intros = [user.get_thirdparty_profile(x).get("intro") for x in config.OPENID_TYPE_DICT.values()]
            intros = filter(None, intros)
            return render_template("post.html", config=config, **locals())
        else:
            abort(403, "没有权限访问该文章")


#TODO:xxx
@app.route("/user")
def user_explore():
    g.count = 24
    user_ids = User.get_ids(start=g.start, limit=g.count)
    users = [User.get(x) for x in user_ids]
    users = [x for x in users if x.get_profile_item('user_privacy') != consts.USER_PRIVACY_PRIVATE]
    return render_template("user_explore.html",
            users=users, config=config)
    
@app.route("/user/<uid>/tag")
def tag(uid):
    u = User.get(uid)
    if not u:
        abort(404, "no such user")
    count = min(g.count, 50)
    kws = get_keywords(u.id, count)
    return ",".join([x[0] for x in kws])
    
@app.route("/logout")
@require_login()
def logout():
    logout_user(g.user)
    flash(u"已退出",  "error")
    return redirect(url_for("home"))

@app.route("/about")
def about():
    return redirect("https://github.com/laiwei/thepast#readme")

@app.route("/connect/", defaults={"provider": config.OPENID_DOUBAN})
@app.route("/connect/<provider>")
def connect(provider):
    d = config.APIKEY_DICT.get(provider)
    login_service = None
    if provider == config.OPENID_DOUBAN:
        login_service = DoubanLogin(d['key'], d['secret'], d['redirect_uri'])
    elif provider == config.OPENID_SINA:
        login_service = SinaLogin(d['key'], d['secret'], d['redirect_uri'])
    elif provider == config.OPENID_QQ:
        login_service = QQOAuth1Login(d['key'], d['secret'], d['redirect_uri'])
    elif provider == config.OPENID_TWITTER:
        login_service = TwitterOAuthLogin(d['key'], d['secret'], d['redirect_uri'])
    try:
        login_uri = login_service.get_login_uri()
    except OAuthLoginError, e:
        return "auth error:%s" % e

    ## when use oauth1, MUST save request_token and secret to SESSION
    if provider == config.OPENID_TWITTER or provider == config.OPENID_QQ:
        login_service.save_request_token_to_session(session)

    return redirect(login_uri)

## 这里其实是所有的登陆入口
@app.route("/connect/<provider>/callback")
def connect_callback(provider):
    code = request.args.get("code")

    d = config.APIKEY_DICT.get(provider)
    login_service = None
    user = None

    if provider in [config.OPENID_DOUBAN, config.OPENID_SINA,]:
        if provider == config.OPENID_DOUBAN:
            openid_type = config.OPENID_TYPE_DICT[config.OPENID_DOUBAN]
            login_service = DoubanLogin(d['key'], d['secret'], d['redirect_uri'])
        elif provider == config.OPENID_SINA:
            openid_type = config.OPENID_TYPE_DICT[config.OPENID_SINA]
            login_service = SinaLogin(d['key'], d['secret'], d['redirect_uri'])

        ## oauth2方式授权处理
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

    else:
        ## 处理以oauth1的方式授权的
        if provider == config.OPENID_QQ:
            user = _qqweibo_callback(request)

        elif provider == config.OPENID_TWITTER:
            user = _twitter_callback(request)

    if user:
        _add_sync_task_and_push_queue(provider, user)
        # 没有email的用户跳转到email补充页面
        if not user.get_email():
            flash(u"请补充一下你的邮箱，PDF文件定期更新之后，会发送到你的邮箱", "error")
            return redirect("/settings")
        return redirect(url_for('index'))
    else:
        flash(u"连接到%s失败了，可能是对方网站忙，请稍等重试..." %provider,  "error")
        return redirect(url_for("home"))


@app.route("/sync/<cates>", methods=["GET", "POST"])
@require_login()
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

def _qqweibo_callback(request):
    d = config.APIKEY_DICT.get(config.OPENID_QQ)
    openid_type = config.OPENID_TYPE_DICT[config.OPENID_QQ]
    login_service = QQOAuth1Login(d['key'], d['secret'], d['redirect_uri'])
    
    ## from qqweibo
    token = request.args.get("oauth_token")
    verifier = request.args.get("oauth_verifier")

    ## from session
    token_secret_pair = login_service.get_request_token_from_session(session)
    if token == token_secret_pair['key']:
        login_service.set_token(token, token_secret_pair['secret'])
    ## get access_token from qq
    token, token_secret  = login_service.get_access_token(verifier)
    user = login_service.get_user_info()

    token_dict = {}
    token_dict['access_token'] = token
    #TODO:这里refresh_token其实就是access_token_secret
    token_dict['refresh_token'] = token_secret
    user = _save_user_and_token(token_dict, user, openid_type)

    return user

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

    ##把各个第三方的uid保存到profile里面
    k = openid_type
    v = {
        "uid": user_info.get_uid(), 
        "intro": user_info.get_intro(),
        "signature": user_info.get_signature(),
        "avatar": user_info.get_avatar(),
        "icon": user_info.get_icon(),
        "email": user_info.get_email(),
    }
    u.set_profile_item(k, json_encode(v))

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

## 添加sync_task任务，并且添加到队列中
def _add_sync_task_and_push_queue(provider, user):
        
    task_ids = [x.category for x in SyncTask.gets_by_user(user)]

    if provider == config.OPENID_DOUBAN:
        if str(config.CATE_DOUBAN_STATUS) not in task_ids:
            t = SyncTask.add(config.CATE_DOUBAN_STATUS, user.id)
            t and TaskQueue.add(t.id, t.kind)

    elif provider == config.OPENID_SINA:
        if str(config.CATE_SINA_STATUS) not in task_ids:
            t = SyncTask.add(config.CATE_SINA_STATUS, user.id)
            t and TaskQueue.add(t.id, t.kind)
    elif provider == config.OPENID_TWITTER:
        if str(config.CATE_TWITTER_STATUS) not in task_ids:
            t = SyncTask.add(config.CATE_TWITTER_STATUS, user.id)
            t and TaskQueue.add(t.id, t.kind)
    elif provider == config.OPENID_QQ:
        if str(config.CATE_QQWEIBO_STATUS) not in task_ids:
            t = SyncTask.add(config.CATE_QQWEIBO_STATUS, user.id)
            t and TaskQueue.add(t.id, t.kind)
