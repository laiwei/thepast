#-*- coding:utf-8 -*-
import datetime

from collections import defaultdict
from flask import g, session, request, \
    redirect, url_for, abort, render_template, flash

from past import config
from past.store import db_conn
from past.corelib import auth_user_from_session, \
        logout_user, category2provider
from past.utils.escape import json_encode
from past.utils.logger import logging

from past.model.user import User, UserAlias, OAuth2Token
from past.model.status import SyncTask, Status, \
        get_status_ids_today_in_history, get_status_ids_yesterday
         
from past.api.error import OAuthError
from past.api.douban import Douban
from past.api.sina import SinaWeibo
from past.api.qqweibo import QQWeibo
from past.api.twitter import TwitterOAuth1

from past.cws.cut import get_keywords
from past import consts

from past import app

from .utils import require_login, check_access_user, statuses_timelize, get_sync_list

log = logging.getLogger(__file__)

@app.before_request
def before_request():
    g.config = config
    g.user = auth_user_from_session(session)
    g.user = User.get(3)
    if g.user:
        g.user_alias = UserAlias.gets_by_user_id(g.user.id)
    else:
        g.user_alias = None

    if g.user:
        unbinded = list(set(config.OPENID_TYPE_DICT.values()) - 
                set([ua.type for ua in g.user.get_alias()]) - set([config.OPENID_TYPE_DICT[config.OPENID_THEPAST]]))
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
        if expired_providers:
            msg = " ".join([x[-1] for x in expired_providers])
            flash(u"你的 %s 授权已经过期了，会影响数据同步，你可以重新授权 :)" % msg, "tip")
    else:
        g.unbinded = None

    g.start = int(request.args.get('start', 0))
    g.count = int(request.args.get('count', 30))
    g.cate = request.args.get("cate", "")
    if not g.cate.isdigit():
        g.cate = ""

@app.teardown_request
def teardown_request(exception):
    #http://stackoverflow.com/questions/9318347/why-are-some-mysql-connections-selecting-old-data-the-mysql-database-after-a-del
    db_conn.commit()

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
    
    try:
        now = datetime.datetime.strptime(request.args.get("now"), "%Y-%m-%d")
    except:
        now = datetime.datetime.now()

    history_ids = get_status_ids_today_in_history(g.user.id, now) 
    status_list = Status.gets(history_ids)
    status_list  = statuses_timelize(status_list)

    sync_list = get_sync_list(g.user)

    d = defaultdict(list)
    for x in status_list:
        t = x.create_time.strftime("%Y年%m月%d日")
        d[t].append(x)
    history_status = d
    
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

@app.route("/reshare_ajax", methods=["POST",])
@require_login()
def reshare():
    text = request.form.get("text", "")
    providers = request.form.get("providers", "").split("|")
    images = request.form.get("images", "").split("|") or []

    ret = {
        "ok": 1,
        "msg": "",
    }
    
    providers_ = []
    for p in config.CAN_SHARED_OPENID_TYPE:
        if p in providers:
            g.user.set_thirdparty_profile_item(p, "share", "Y")
            providers_.append(p)
        else:
            g.user.set_thirdparty_profile_item(p, "share", "N")

    failed_providers = []
    for p in providers_:
        try:
            post_status(g.user, p, text + ",".join(images))
        except OAuthError, e:
            log.warning("%s" % e)
            failed_providers.append(config.OPENID_TYPE_NAME_DICT.get(p, ""))
    if failed_providers:
        ret['ok'] = 0
        ret['msg'] = "分享到" + ",".join(failed_providers) + "失败了，可能是授权过期了，重新授权就ok：）"
    return json_encode(ret)


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

def post_status(user, provider=None, msg=""):
    if msg and isinstance(msg, unicode):                                           
        msg = msg.encode("utf8") 
    if not provider or provider == config.OPENID_TYPE_DICT[config.OPENID_DOUBAN]:
        print "++++++++++post douban status"
        client = Douban.get_client(user.id)
        if client:
            if not msg:
                msg = "#thepast.me# 你好，旧时光| 我在用thepast, 广播备份，往事提醒，你也来试试吧 >> http://thepast.me "
            client.post_status(msg)

    if not provider or provider == config.OPENID_TYPE_DICT[config.OPENID_SINA]:
        print "++++++++++post sina status"
        client = SinaWeibo.get_client(user.id)
        if client:
            if not msg:
                msg = "#thepast.me# 你好，旧时光| 我在用thepast, 微博备份，往事提醒，你也来试试吧 >> http://thepast.me "
            client.post_status(msg)

    if not provider or provider == config.OPENID_TYPE_DICT[config.OPENID_TWITTER]:
        print "++++++++post twitter status"
        client = TwitterOAuth1.get_client(user.id)
        if client:
            if not msg:
                msg = "#thepast.me# 你好，旧时光| 我在用thepast, twitter备份，往事提醒，你也来试试吧 >> http://thepast.me "
            client.post_status(msg)

    if not provider or provider == config.OPENID_TYPE_DICT[config.OPENID_QQ]:
        print "++++++++post qq weibo status"
        client = QQWeibo.get_client(user.id)
        if client:
            if not msg:
                msg = "#thepast.me# 你好，旧时光| 我在用thepast, 微博备份，往事提醒，你也来试试吧 >> http://thepast.me "
            client.post_status(msg)
