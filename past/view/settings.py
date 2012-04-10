#-*- coding:utf-8 -*-

#past.view.settings

from flask import g, flash, request, render_template, redirect
from past import app
from past import config
from past.model.user import User, Confirmation, UserAlias
from past.model.status import SyncTask, TaskQueue
from past.utils import is_valid_email
from past.utils.escape import json_encode
from past.utils import randbytes
from past.api_client import Wordpress
from past.store import mc

from .utils import require_login

@app.route("/settings", methods=["GET", "POST"])
@require_login("/settings")
def settings():
    g.user = User.get(5)
    ##XXX:
    intros = [g.user.get_thirdparty_profile(x).get("intro") for x in config.OPENID_TYPE_DICT.values()]
    intros = filter(None, intros)

    uas = g.user.get_alias()
    wordpress_alias_list = [x for x in uas if x.type == config.OPENID_TYPE_DICT[config.OPENID_WORDPRESS]]
    wordpress_alias = wordpress_alias_list and wordpress_alias_list[0]

    if request.method == "POST":
        email = request.form.get("email")
        if email and is_valid_email(email):
            r = g.user.set_email(email)
            if r:
                flash(u'个人信息更新成功', 'tip')
            else:
                flash(u'电子邮箱已被占用了', 'error')
        else:
            flash(u'电子邮箱格式不正确', 'error')
    return render_template("settings.html", **locals())


@app.route("/bind/wordpress", methods=["GET", "POST"])
def bind_wordpress():
    if not g.user:
        flash(u"请先使用豆瓣、微博、QQ、Twitter任意一个帐号登录后，再来做绑定blog的操作^^", "tip")
        return redirect("/home")

    uas = g.user.get_alias()
    wordpress_alias_list = [x for x in uas if x.type == config.OPENID_TYPE_DICT[config.OPENID_WORDPRESS]]

    step = "1"
    random_id = mc.get("wordpress_bind:%s" % g.user.id)
    c = random_id and Confirmation.get_by_random_id(random_id)
    if c:
        _, feed_uri = c.text.split(":", 1)
        step = "2"
    else:
        feed_uri = ""
    

    if request.method == "GET":
        return render_template("bind_wordpress.html", **locals())
    
    elif request.method == "POST":
        ret = {}
        ret['ok'] = False
        if step == '1':
            feed_uri = request.form.get("feed_uri")
            if not feed_uri:
                ret['msg'] = 'feed地址不能为空'
            elif not (feed_uri.startswith("http://") or feed_uri.startswith("https://")):
                ret['msg'] = 'feed地址貌似不对'
            else:
                ua = UserAlias.get(config.OPENID_TYPE_DICT[config.OPENID_WORDPRESS], feed_uri)
                if ua:
                    ret['msg'] = '该feed地址已被绑定'
                else:
                    ##设置一个激活码
                    code = randbytes(16)
                    val = "%s:%s" % (g.user.id, feed_uri)
                    r = Confirmation.add(code, val)
                    if r:
                        ret['ok'] = True
                        ret['msg'] = '为了验证blog的主人^^，请发一篇blog，内容为 %s，完成该步骤后，请点下一步完成绑定' \
                                % code
                        mc.set("wordpress_bind:%s" %g.user.id, code)
                    else:
                        ret['msg'] = '抱歉，出错了，请重试'
            return json_encode(ret)
        elif step == '2':
            if not (random_id and c):
                ret['msg'] = '出错了，激活码不对^^'
            else:
                text = c.text
                user_id, feed_uri = text.split(":", 1)
                ## 同步一下，看看验证码的文章是否正确
                client = Wordpress(feed_uri)
                rs = client.get_feeds(refresh=True)
                if not rs:
                    ret['msg'] = '没有发现含有验证码的文章，请检查后再提交验证'
                else:
                    latest_post = rs[0]
                    if latest_post.get_content().encode("utf8")[:100].find(str(random_id)) == -1:
                        ret['msg'] = "没有发现含有验证码的文章，请检查后再提交验证"
                    else:
                        ua = UserAlias.bind_to_exists_user(g.user, 
                                config.OPENID_TYPE_DICT[config.OPENID_WORDPRESS], feed_uri)
                        if not ua:
                            ret['msg'] = '出错了，麻烦你重试一下吧^^'
                        else:
                            ##添加同步任务
                            t = SyncTask.add(config.CATE_WORDPRESS_POST, g.user.id)
                            t and TaskQueue.add(t.id, t.kind)
                            ##删除confiration记录
                            c.delete()
                            mc.delete("wordpress_bind:%s" %g.user.id)

                            ret['ok'] = True
                            ret['msg'] = '恭喜，绑定成功啦'
            return json_encode(ret)
    else:
        return "method not allowed"
