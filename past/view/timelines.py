#-*- coding:utf-8 -*-
import os
from datetime import datetime, timedelta
import calendar
import time
from collections import defaultdict

from flask import g, request, redirect, url_for, abort, render_template,\
        make_response, flash

from past import app
from past import config
from past.model.user import User, PdfSettings
from past.model.status import Status

from past.utils import sizeof_fmt
from past.utils.pdf import is_pdf_file_exists, get_pdf_filename, get_pdf_full_filename
from past.utils.escape import json_encode
from past import consts
from .utils import require_login, check_access_user, statuses_timelize, get_sync_list

@app.route("/i")
@require_login()
def timeline():
    redir = "/%s" %g.user.uid 
    if g.cate:
        redir = "%s?cate=%s" % (redir, g.cate)
    return redirect(redir)

@app.route("/user/<uid>")
def user(uid):
    u = User.get(uid)
    if not u:
        abort(404, "no such user")
    return redirect("/%s" % uid)

@app.route("/<uid>")
def user_by_domain(uid):
    u = User.get(uid)
    if not u:
        abort(404, "no such user")

    r = check_access_user(u)
    if r:
        flash(r[1].decode("utf8"), "tip")
        return redirect(url_for("home"))

    ids = Status.get_ids(user_id=u.id, start=g.start, limit=g.count, cate=g.cate)
    status_list = Status.gets(ids)
    if g.user and g.user.id == uid:
        pass
    elif g.user and g.user.id != uid:
        status_list = [x for x in status_list if x.privacy() != consts.STATUS_PRIVACY_PRIVATE]
    elif not g.user:
        status_list = [x for x in status_list if x.privacy() == consts.STATUS_PRIVACY_PUBLIC]
        
    status_list  = statuses_timelize(status_list)
    tags_list = []
    intros = [u.get_thirdparty_profile(x).get("intro") for x in config.OPENID_TYPE_DICT.values()]
    intros = filter(None, intros)

    if g.user:
        sync_list = get_sync_list(g.user)
    else:
        sync_list = []

    return render_template("timeline.html", user=u, unbinded=[], 
            tags_list=tags_list, intros=intros, 
            status_list=status_list, config=config, sync_list=sync_list)

@app.route("/pdf")
@require_login()
def mypdf():
    if not g.user:
        return redirect(url_for("pdf", uid=config.MY_USER_ID))
    else:
        return redirect(url_for("pdf", uid=g.user.id))

@app.route("/pdf/apply", methods=["POST"])
@require_login()
def pdf_apply():
    delete = request.form.get("delete")
    if delete:
        PdfSettings.remove_user_id(g.user.id)
        flash(u"删除PDF的请求提交成功，系统会在接下来的一天里删除掉PDF文件！", "tip")
        return redirect("/pdf")
    else:
        PdfSettings.add_user_id(g.user.id)
        flash(u"申请已通过，请明天早上来下载数据吧！", "tip")
        return redirect("/pdf")


@app.route("/demo-pdf")
def demo_pdf():
    pdf_filename = "demo.pdf"
    full_file_name = os.path.join(config.PDF_FILE_DOWNLOAD_DIR, pdf_filename)
    resp = make_response()
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = 'attachment; filename=%s' % pdf_filename
    resp.headers['Content-Length'] = os.path.getsize(full_file_name)
    redir = '/down/pdf/' + pdf_filename
    resp.headers['X-Accel-Redirect'] = redir
    return resp
    
#PDF只允许登录用户查看
@app.route("/<uid>/pdf")
@require_login()
def pdf(uid):
    user = User.get(uid)
    if not user:
        abort(404, "No such user")

    if uid != g.user.id and user.get_profile_item('user_privacy') == consts.USER_PRIVACY_PRIVATE:
        flash(u"由于该用户设置了仅自己可见的权限，所以，我们就看不到了", "tip")
        return redirect(url_for("timeline"))

    intros = [g.user.get_thirdparty_profile(x).get("intro") for x in config.OPENID_TYPE_DICT.values()]
    intros = filter(None, intros)

    pdf_files = []
    start_date = Status.get_oldest_create_time(None, user.id)
    now = datetime.now()
    d = start_date
    while d and d <= now:
        pdf_filename = get_pdf_filename(user.id, d.strftime("%Y%m"))
        if is_pdf_file_exists(pdf_filename):
            full_file_name = get_pdf_full_filename(pdf_filename)
            pdf_files.append([d, pdf_filename, sizeof_fmt(os.path.getsize(full_file_name))])

        days = calendar.monthrange(d.year, d.month)[1]
        d += timedelta(days=days)
        d = datetime(d.year, d.month, 1)
    files_dict = defaultdict(list)
    for date, filename, filesize in pdf_files:
        files_dict[date.year].append([date, filename, filesize])

    pdf_applyed = PdfSettings.is_user_id_exists(g.user.id)
    return render_template("pdf.html", **locals())

@app.route("/pdf/<filename>")
@require_login()
def pdf_down(filename):
    pdf_filename = filename
    if not is_pdf_file_exists(pdf_filename):
        abort(404, "Please wait one day to  download the PDF version, because the vps memory is limited")

    user_id = pdf_filename.split('_')[1]
    u = User.get(user_id)
    if not u:
        abort(400, 'Bad request')

    if user_id != g.user.id and u.get_profile_item('user_privacy') == consts.USER_PRIVACY_PRIVATE:
        abort(403, 'Not allowed')

    full_file_name = get_pdf_full_filename(pdf_filename)
    resp = make_response()
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = 'attachment; filename=%s' % pdf_filename
    resp.headers['Content-Length'] = os.path.getsize(full_file_name)
    redir = '/down/pdf/' + pdf_filename
    resp.headers['X-Accel-Redirect'] = redir
    return resp

