#-*- coding:utf-8 -*-

from flask import (session, redirect, request, abort, g, url_for, flash)
from past import config
from past.corelib import set_user_cookie 

from past.model.user import User, UserAlias, OAuth2Token
from past.model.status import SyncTask, TaskQueue

from past.api.douban import Douban
from past.api.sina import SinaWeibo
from past.api.qqweibo import QQWeibo
from past.api.renren import Renren
from past.api.instagram import Instagram
from past.api.twitter import TwitterOAuth1
from past.api.wordpress import Wordpress
from past.api.error import OAuthError

from past.utils.escape import json_encode
from past.connect import blue_print

from past.utils.logger import logging
log = logging.getLogger(__file__)

@blue_print.route("/",  defaults={"provider": config.OPENID_DOUBAN})
@blue_print.route("/<provider>")
def connect(provider):
    if provider == "renren":
        return "我已经实在受不了人人，被人人的管理员快搞死了，怎么修改都不通过，唉...  有兴趣可以看看这边豆瓣网友的帖子：http://www.douban.com/note/250372684/"
    #return "thepast.me 正在升级硬件，暂时不提供登录、注册功能，请谅解，有问题请邮件到 help@thepast.me"

    client = None
    if provider == config.OPENID_DOUBAN:
        client = Douban()
    elif provider == config.OPENID_SINA:
        client = SinaWeibo()
    elif provider == config.OPENID_TWITTER:
        client = TwitterOAuth1()
    elif provider == config.OPENID_QQ:
        client = QQWeibo()
    elif provider == config.OPENID_RENREN:
        client = Renren()
    elif provider == config.OPENID_INSTAGRAM:
        client = Instagram()
    if not client:
        abort(400, "不支持该第三方登录")

    try:
        login_uri = client.login()
    except OAuthError, e:
        log.warning(e)
        abort(400, "抱歉，跳转到第三方失败，请重新尝试一下:)")

    ## when use oauth1, MUST save request_token and secret to SESSION
    if provider == config.OPENID_TWITTER or provider == config.OPENID_QQ:
        client.save_request_token_to_session(session)

    return redirect(login_uri)

@blue_print.route("/<provider>/callback")
def connect_callback(provider):
    code = request.args.get("code")

    client = None
    user = None

    openid_type = config.OPENID_TYPE_DICT.get(provider)
    if not openid_type:
        abort(404, "not support such provider")

    if provider in [config.OPENID_DOUBAN, config.OPENID_SINA, config.OPENID_RENREN,
            config.OPENID_INSTAGRAM,]:
        if provider == config.OPENID_DOUBAN:
            client = Douban()
        elif provider == config.OPENID_SINA:
            client = SinaWeibo()
        elif provider == config.OPENID_RENREN:
            client = Renren()
        elif provider == config.OPENID_INSTAGRAM:
            client = Instagram()

        ## oauth2方式授权处理
        try:
            token_dict = client.get_access_token(code)
            print "---token_dict", token_dict
        except OAuthError, e:
            log.warning(e)
            abort(400, u"从第三方获取access_token失败了，请重新尝试一下，抱歉:)")

        if not (token_dict and token_dict.get("access_token")):
            abort(400, "no_access_token")
        try:
            access_token = token_dict.get("access_token", "") 
            refresh_token = token_dict.get("refresh_token", "") 
            #the last is instagram case:)
            uid = token_dict.get("uid") or token_dict.get("user", {}).get("uid") \
                    or token_dict.get("user", {}).get("id")
            client.set_token(access_token, refresh_token)
            user_info = client.get_user_info(uid)
            print "---user_info", user_info, user_info.data
        except OAuthError, e:
            log.warning(e)
            abort(400, u"我已经实在受不了人人，被人人的管理员快搞死了，怎么修改都不通过，唉")

        user = _save_user_and_token(token_dict, user_info, openid_type)

    else:
        ## 处理以oauth1的方式授权的
        if provider == config.OPENID_QQ:
            user = _qqweibo_callback(request)

        elif provider == config.OPENID_TWITTER:
            user = _twitter_callback(request)

    if user:
        _add_sync_task_and_push_queue(provider, user)

        if not user.get_email():
            return redirect("/settings")

        return redirect("/")
    else:
        flash(u"连接到%s失败了，可能是对方网站忙，请稍等重试..." %provider,  "error")
        return redirect("/")

def _qqweibo_callback(request):
    openid_type = config.OPENID_TYPE_DICT[config.OPENID_QQ]
    client = QQWeibo()
    
    ## from qqweibo
    token = request.args.get("oauth_token")
    verifier = request.args.get("oauth_verifier")

    ## from session
    token_secret_pair = client.get_request_token_from_session(session)
    if token == token_secret_pair['key']:
        client.set_token(token, token_secret_pair['secret'])
    ## get access_token from qq
    token, token_secret  = client.get_access_token(verifier)
    user = client.get_user_info()

    token_dict = {}
    token_dict['access_token'] = token
    #TODO:这里refresh_token其实就是access_token_secret
    token_dict['refresh_token'] = token_secret
    user = _save_user_and_token(token_dict, user, openid_type)

    return user

def _twitter_callback(request):
    openid_type = config.OPENID_TYPE_DICT[config.OPENID_TWITTER]
    client = TwitterOAuth1()

    ## from twitter
    code = request.args.get("oauth_code") ## FIXME no use
    verifier = request.args.get("oauth_verifier")
    
    ## from session
    request_token = client.get_request_token_from_session(session)
    
    ## set the authorized request_token to OAuthHandle
    client.auth.set_request_token(request_token.get("key"), 
            request_token.get("secret"))

    ## get access_token
    try:
        token_dict = client.get_access_token(verifier)
    except OAuthError, e:
        abort(401, e.msg)

    thirdparty_user = client.get_user_info()
    
    user = _save_user_and_token(token_dict, thirdparty_user, openid_type)
    return user
    
## 保存用户信息到数据库，并保存token
def _save_user_and_token(token_dict, thirdparty_user, openid_type):
    first_connect = False
    ua = UserAlias.get(openid_type, thirdparty_user.get_user_id())
    if not ua:
        if not g.user:
            ua = UserAlias.create_new_user(openid_type,
                    thirdparty_user.get_user_id(), thirdparty_user.get_nickname())
        else:
            ua = UserAlias.bind_to_exists_user(g.user, 
                    openid_type, thirdparty_user.get_user_id())
        first_connect = True
    if not ua:
        return None

    ##设置个人资料（头像等等）
    u = User.get(ua.user_id)
    u.set_avatar_url(thirdparty_user.get_avatar())
    u.set_icon_url(thirdparty_user.get_icon())

    ##把各个第三方的uid保存到profile里面
    k = openid_type
    v = {
        "uid": thirdparty_user.get_uid(), 
        "name": thirdparty_user.get_nickname(), 
        "intro": thirdparty_user.get_intro(),
        "signature": thirdparty_user.get_signature(),
        "avatar": thirdparty_user.get_avatar(),
        "icon": thirdparty_user.get_icon(),
        "email": thirdparty_user.get_email(),
        "first_connect": "Y" if first_connect else "N",
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
    elif provider == config.OPENID_RENREN:
        for cate in (config.CATE_RENREN_STATUS, config.CATE_RENREN_BLOG, 
                config.CATE_RENREN_ALBUM, config.CATE_RENREN_PHOTO):
            if str(cate) not in task_ids:
                t = SyncTask.add(cate, user.id)
                t and TaskQueue.add(t.id, t.kind)
    elif provider == config.OPENID_INSTAGRAM:
        if str(config.CATE_INSTAGRAM_STATUS) not in task_ids:
            t = SyncTask.add(config.CATE_INSTAGRAM_STATUS, user.id)
            t and TaskQueue.add(t.id, t.kind)

