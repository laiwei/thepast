#-*- coding:utf-8 -*-
import os
import datetime
import re
from functools import wraps
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from flask import g, session, request, send_from_directory, \
    redirect, url_for, abort, render_template, make_response, flash

import config
from past.corelib import auth_user_from_session, set_user_cookie, \
        logout_user, category2provider
from past.utils.escape import json_encode, json_decode, clear_html_element
from past.utils.pdf import link_callback, is_pdf_file_exists, generate_pdf, get_pdf_filename, is_user_pdf_file_exists
from past.model.user import User, UserAlias, OAuth2Token
from past.model.status import SyncTask, Status, TaskQueue
from past.oauth_login import DoubanLogin, SinaLogin, OAuthLoginError,\
        TwitterOAuthLogin, QQOAuth1Login
import api_client

from past import app

def require_login(f):
    @wraps(f)
    def _(*a, **kw):
        if not g.user:
            return redirect(url_for("login"))

        return f(*a, **kw)
    return _

@app.before_request
def before_request():
    g.user = auth_user_from_session(session)
    if g.user:
        g.user_alias = UserAlias.gets_by_user_id(g.user.id)
    else:
        g.user_alias = None
    g.start = int(request.args.get('start', 0))
    g.count = int(request.args.get('count', 30))
    g.cate = request.args.get("cate", None)

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
        return redirect(url_for("user_explore"))

    ids = Status.get_ids(user_id=g.user.id, start=g.start, limit=g.count, cate=g.cate)
    status_list = Status.gets(ids)
    status_list  = statuses_timelize(status_list)
    return render_template("timeline.html", user=g.user, status_list=status_list, config=config)

@app.route("/user")
def user_explore():
    user_ids = User.get_ids(start=g.start, limit=g.count)
    users = [User.get(x) for x in user_ids]
    return render_template("user_explore.html", users=users, config=config)
    

@app.route("/user/<uid>")
@require_login
def user(uid):
    u = User.get(uid)
    if not u:
        abort(404, "no such user")

    if g.user and g.user.id == u.id:
        return redirect(url_for("index"))
    
    #TODO:增加可否查看其他用户的权限检查
    cate = request.args.get("cate", None)
    ids = Status.get_ids(user_id=u.id, start=g.start, limit=g.count, cate=g.cate)
    status_list = Status.gets(ids)
    status_list  = statuses_timelize(status_list)
    return render_template("timeline.html", user=u, status_list=status_list, config=config)

@app.route("/settings/profile")
@require_login
def profile():
    u = g.user
    sync_tasks = SyncTask.gets_by_user(u)
    my_sync_cates = [x.category for x in sync_tasks]
    return render_template("profile.html", user=u, 
            my_sync_cates = my_sync_cates, config=config)

@app.route("/logout")
@require_login
def logout():
    r = logout_user(g.user)
    flash(u"已退出",  "error")
    return redirect(url_for("login"))

#TODO
@app.route("/login")
def login():
    if g.user:
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/about")
def about():
    return render_template("about.html")

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
        print '------- connect, client:', login_service

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
    else:
        ## 处理以oauth1的方式授权的
        if provider == config.OPENID_QQ:
            user = _qqweibo_callback(request)

        elif provider == config.OPENID_TWITTER:
            user = _twitter_callback(request)

        if user:
            _add_sync_task_and_push_queue(provider, user)
            return redirect(url_for('index'))
        else:
            return "connect to %s fail" % provider

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
        _add_sync_task_and_push_queue(provider, user)
        return redirect(url_for('index'))
    else:
        flash(u"连接到%s失败了，可能是对方网站忙，请稍等重试..." %provider,  "error")
        return redirect(url_for("login"))

@app.route("/sync/<cates>", methods=["GET", "POST"])
@require_login
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

@app.route("/pdf")
@require_login
def mypdf():
    if not g.user:
        return redirect(url_for("pdf", uid=config.MY_USER_ID))
    else:
        return redirect(url_for("pdf", uid=g.user.id))

@app.route("/<uid>/pdf")
@require_login
def pdf(uid):
    user = User.get(uid)
    if not user:
        abort(404, "No such user")
    
    pdf_filename = get_pdf_filename(user.id)
    if not is_pdf_file_exists(pdf_filename):
        #generate_pdf(pdf_filename, user.id, 0, 10000000)
        #abort(404, u"请明天来下载吧，因为我的内存吃不消了，只能晚上生成PDF^^")
        abort(404, "Please wait one day to  download the PDF version, because the vps memory is limited")
    if not is_pdf_file_exists(pdf_filename):
        abort(400, "generate pdf fail, please try again...")

    full_file_name = os.path.join(config.PDF_FILE_DOWNLOAD_DIR, pdf_filename)
    resp = make_response()
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = 'attachment; filename=%s' % pdf_filename
    resp.headers['Content-Length'] = os.path.getsize(full_file_name)
    redir = '/down/pdf/' + pdf_filename
    resp.headers['X-Accel-Redirect'] = redir
    return resp

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
            if str(config.CATE_DOUBAN_MINIBLOG) not in task_ids:
                t = SyncTask.add(config.CATE_DOUBAN_MINIBLOG, user.id)
                t and TaskQueue.add(t.id, t.kind)
            if str(config.CATE_DOUBAN_NOTE) not in task_ids:
                t = SyncTask.add(config.CATE_DOUBAN_NOTE, user.id)
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

## 把status_list构造为month，day的层级结构
def statuses_timelize(status_list):

    hashed = {}
    for s in status_list:
        hash_s = hash(s)
        if hash_s not in hashed:
            hashed[hash_s] = RepeatedStatus(s)
        else:
            hashed[hash_s].status_list.append(s)

    output = {}
    for hash_s, repeated in hashed.items():
        s = repeated.status_list[0]
        year_month = "%s-%s" % (s.create_time.year, s.create_time.month)
        day = s.create_time.day

        if year_month not in output:
            output[year_month] = {day:[repeated]}
        else:
            if day not in output[year_month]:
                output[year_month][day] = [repeated]
            else:
                output[year_month][day].append(repeated)

    return output

class RepeatedStatus(object):
    def __init__(self, status):
        self.create_time = status.create_time
        self.status_list = [status]
