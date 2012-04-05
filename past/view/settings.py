#-*- coding:utf-8 -*-

#past.view.settings

from flask import g, flash, request, render_template, redirect
from past import app
from past import config
from past.model.user import User
from past.utils import is_valid_email

from .utils import require_login

@app.route("/settings", methods=["GET", "POST"])
@require_login("/settings")
def settings():
    intros = [g.user.get_thirdparty_profile(x).get("intro") for x in config.OPENID_TYPE_DICT.values()]
    intros = filter(None, intros)

    if request.method == "POST":
        email = request.form.get("email")
        if email and is_valid_email(email):
            r = g.user.set_email(email)
            if r:
                flash(u'个人信息更新成功', 'tip')
            else:
                flash(u'电子邮箱已被占用了', 'error')
        else:
            flash(u'电子邮箱更新失败', 'error')
    return render_template("settings.html", **locals())

