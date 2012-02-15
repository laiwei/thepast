#-*- coding:utf-8 -*-
import os
import datetime
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from flask import g, session, request, send_from_directory, \
    redirect, url_for, abort, render_template, make_response, flash

import config
from past.corelib import auth_user_from_session, set_user_cookie, \
    logout_user, category2provider
from past.utils.escape import json_encode, json_decode
from past.utils import link_callback, wrap_long_line, filters, save_pdf, randbytes
from past.model.user import User, UserAlias, OAuth2Token
from past.model.status import SyncTask, Status, TaskQueue
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
        return redirect(url_for("login"))

    ids = Status.get_ids(user_id=g.user.id, start=g.start, limit=g.count, cate=g.cate)
    status_list = Status.gets(ids)
    return render_template("timeline.html", user=g.user, status_list=status_list, config=config)

@app.route("/user")
def user_explore():
    user_ids = User.get_ids(start=g.start, limit=g.count)
    users = [User.get(x) for x in user_ids]
    return render_template("user_explore.html", users=users, config=config)
    

@app.route("/user/<uid>")
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
        if user:
            _add_sync_task_and_push_queue(provider, user)
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
        _add_sync_task_and_push_queue(provider, user)
        return redirect(url_for('index'))
    else:
        flash("连接到%s失败了，可能是对方网站忙，请稍等重试..." %provider,  "error")
        return redirect(url_for("login"))

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

@app.route("/pdf")
def mypdf():
    if not g.user:
        return redirect(url_for("pdf", uid=config.MY_USER_ID))
    else:
        return redirect(url_for("pdf", uid=g.user.id))

@app.route("/<uid>/pdf")
def pdf(uid):
    from xhtml2pdf.default import DEFAULT_FONT
    from xhtml2pdf.document import pisaDocument

    #########Set FONT################
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont('zhfont', os.path.join(app.root_path, 'static/font/yahei-consolas.ttf')))
    DEFAULT_FONT["helvetica"]="zhfont"
    css = open(os.path.join(app.root_path, "static/css/pdf.css")).read()

    result = StringIO.StringIO()

    user = User.get(uid)
    if not g.user:
        ##匿名用户暂时只能看我的作为演示
        g.count = min(25, g.count)
        user = User.get(config.MY_USER_ID)
    else:
        if g.user.id == user.id:
            if g.count < 60:
                g.count = 60
            g.count = min(100, g.count)
        else:
            ##登录用户只能生成别人的25条
            g.count = min(25, g.count)

    # get status
    ids = Status.get_ids(user_id=uid, start=g.start, limit=g.count, cate=g.cate)
    status_list = Status.gets(ids)

    _html = u"""<html> <body>
        <div id="Top">
            <img src="%s"/> &nbsp; &nbsp;&nbsp; The Past of Me | 个人杂志计划&nbsp;&nbsp;&nbsp;%s&nbsp;&nbsp;&nbsp;CopyRight©%s
            <br/>
        </div>
        <br/> <br/>

        <div class="box">
    """ %(os.path.join(app.root_path, "static/img/logo.png"), 
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user.name)

    for s in status_list:
        title = s.title
        create_time = s.create_time
        from_ = ''
        if s.category == config.CATE_DOUBAN_MINIBLOG:
            from_ = u'<a href="' + config.DOUBAN_MINIBLOG %(s.origin_user_id, s.origin_id) + u'class="node">From：豆瓣广播</a>'
        elif s.category == config.CATE_DOUBAN_NOTE:
            from_ = u'<a href="' + config.DOUBAN_NOTE %(s.origin_id,) + u'class="node">From：豆瓣日记</a>'
        elif s.category == config.CATE_SINA_STATUS:
            from_ = u'<a href="' + config.WEIBO_STATUS %(s.origin_id) + u'class="node">From：新浪微博</a>'
        elif s.category == config.CATE_TWITTER_STATUS:
            from_ = u'<a href="' + config.TWITTER_STATUS %(s.origin_id) + u'class="node">From：twitter</a>'
        text = s.text
        retweeted_text = ''
        img = ''
        if s.category == config.CATE_DOUBAN_MINIBLOG:
            ##miniblog不显示title
            title = ''
            links = s.get_data().get_links()
            if links and links.get("image"):
                img = links.get("image")
        elif s.category == config.CATE_SINA_STATUS:
            retweeted = s.get_data().get_retweeted_status()
            re_mid_pic = retweeted and retweeted.get_middle_pic() or ''
            middle_pic = s.get_data().get_middle_pic()

            if retweeted:
                retweeted_text = retweeted.get_user().get_nickname() + ": " + retweeted.get_content()
                    
            if re_mid_pic or middle_pic:
                img = re_mid_pic or middle_pic
        
        _html += """ <hr/> <div class="cell">"""
        if title:
            title = wrap_long_line(title)
            _html += """<div class="bigger">%s</div>""" %title
        if text:
            text = wrap_long_line(text)
            if s.category == config.CATE_DOUBAN_NOTE:
                text = filters.nl2br(text)
            _html += """<div class="content">%s</div>""" %text
        if retweeted_text:
            retweeted_text = wrap_long_line(retweeted_text)
            _html += """<div class='tip'><span class="fade">%s</span></div>""" %retweeted_text
        if img:
            _html += """<img src=%s></img>""" %img
        _html += """<div class="fade">%s &nbsp;&nbsp;&nbsp; %s</div>""" %(from_, create_time)
        _html += """ </div> <body> </html> """

    _pdf = pisaDocument(_html, result, default_css=css, link_callback=link_callback)

    if not _pdf.err:
        result.seek(0)
        pdf_filename = "thepast.me_pdf_%s%s.pdf" %(user.id, randbytes(6))
        save_pdf(result.getvalue(), pdf_filename)
        #resp = make_response(result.getvalue())
        #resp.headers["content-type"] = "application/pdf"
        resp = make_response()
        resp.headers['Cache-Control'] = 'no-cache'
        resp.headers['Content-Type'] = 'application/pdf'
        redir = '/down/pdf/' + pdf_filename
        resp.headers['X-Accel-Redirect'] = redir
        return resp
    else:
        return 'pdf error: %s' %_pdf.err

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

